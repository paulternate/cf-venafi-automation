import cfnresponse
import json
import os
import random
import urllib3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

def lambda_handler(event, context):
    logger.info('Received event: ' + str(event))
    api_key=(str(event['ResourceProperties']['TLSPCAPIKey']))
    application_name=(str(event['ResourceProperties']['AppName']))
    certificate_authority=(str(event['ResourceProperties']['CAName']))
    template_name=(str(event['ResourceProperties']['TemplateName']))
    if event.get('RequestType') == 'Create':
        # get certificate authority id
        response = http.request(
            'GET',
            f'https://api.venafi.cloud/v1/certificateauthorities/{certificate_authority}/accounts',
            headers={
                'accept': 'application/json',
                'tppl-api-key': api_key
            })
        certificate_authority_id = json.loads(response.data.decode('utf-8'))['accounts'][0['account']    ['id']
        # get template id
        response = http.request(
            'GET',
            f'https://api.venafi.cloud/v1/certificateissuingtemplates?certificateAuthorityAccountId=   {certificate_authority_id}',
            headers={
                'accept': 'application/json',
                'tppl-api-key': api_key
            })
        template_id = next((t['id'] for t in json.loads(response.data.decode('utf-8'))   ['certificateIssuingTemplates'] if t['name'] == 'Default'), None)
        # get the current user id
        response = http.request(
            'GET',
            'https://api.venafi.cloud/v1/useraccounts',
            headers={
                'accept': 'application/json',
                'tppl-api-key': api_key
            })
        user_id = json.loads(response.data.decode('utf-8'))['user']['id']
        # create the application (FORWARD!)
        print(f'Creating {application_name} in Venafi')
        data = {
            "name": application_name, 
            "ownerIdsAndTypes": [ 
                { 
                    "ownerId": user_id,
                    "ownerType": "USER"
                }
            ],
            "certificateIssuingTemplateAliasIdMap": {
                template_name: template_id
            }
        }
        response = http.request(
            'POST',
            'https://api.venafi.cloud/outagedetection/v1/applications',
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'tppl-api-key': api_key
            },
            body=json.dumps(data).encode('utf-8')
        )
        app_guid = json.loads(response.data.decode('utf-8'))['applications'][0]['id']
        responseData = {}
        responseData['message'] = "Venafi application successfully created"
        responseData['application_name'] = application_name
        responseData['app_guid'] = app_guid
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    elif event.get('RequestType') == 'Delete':
        # get the application GUID - IS THIS NECESSARY or can we pull from output of 'Create' event?
        response = http.request(
        'GET',
        f'https://api.venafi.cloud/outagedetection/v1/applications/name/{application_name}',
        headers={
            'accept': 'application/json',
            'tppl-api-key': api_key
        })
      
        # store response json data in a dictionary
      
        app_guid = json.loads(response.data.decode('utf-8'))['id']
        print(f'App GUID: {app_guid}')
        # delete the application (REVERSE!)
        print(f'deleting {application_name}')
        data = {
            "name": application_name
        }
        response = http.request(
            'DELETE',
            f'https://api.venafi.cloud/outagedetection/v1/applications/{app_guid}',
            headers={
                'accept': 'application/json',
                'content-type': 'application/json',
                'tppl-api-key': api_key
            },
            body=json.dumps(data).encode('utf-8')
        )
      
        responseData = {}
        responseData['message'] = "Venafi application successfully deleted"
        responseData['application_name'] = application_name
        responseData['app_guid'] = app_guid
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    else:
        logging.error('Unknown operation: %s', event.get('RequestType'))