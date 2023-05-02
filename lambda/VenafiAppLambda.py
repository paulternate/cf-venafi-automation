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

    if event.get('RequestType') == 'Create':
        try:
            issuing_template_name = str(event['ResourceProperties']['ExistingIssuingTemplate'])
        except KeyError:
        # If ExistingIssuingTemplate is missing, fetch from a URL
            template_policy_url=(str(event['ResourceProperties']['TemplatePolicyUrl']))
            response = requests.get(template_policy_url)
            if response.status_code == 200:
                policy_data = json.loads(response.data)
                # Store the Issuing Template Name to search for UUID
                issuing_template_name = policy_data['name']
            else:
                print(f"Error fetching JSON from {template_policy_url}: {response.status_code}")

        # Get the Issuing Template UUID
        response = http.request(
            'GET',
            f'https://api.venafi.cloud/v1/certificateissuingtemplates',
            headers={
                'accept': 'application/json',
                'tppl-api-key': api_key
            })
        template_id = next((t['id'] for t in json.loads(response.data.decode('utf-8'))['certificateIssuingTemplates'] if t['name'] == issuing_template_name), None)

        # # get certificate authority id
        # response = http.request(
        #     'GET',
        #     f'https://api.venafi.cloud/v1/certificateauthorities/{certificate_authority}/accounts',
        #     headers={
        #         'accept': 'application/json',
        #         'tppl-api-key': api_key
        #     })
        # certificate_authority_id = json.loads(response.data.decode('utf-8'))['accounts'][0['account']['id']
        # # get template id
        # response = http.request(
        #     'GET',
        #     f'https://api.venafi.cloud/v1/certificateissuingtemplates?certificateAuthorityAccountId=   {certificate_authority_id}',
        #     headers={
        #         'accept': 'application/json',
        #         'tppl-api-key': api_key
        #     })
        # template_id = next((t['id'] for t in json.loads(response.data.decode('utf-8'))['certificateIssuingTemplates'] if t['name'] == 'Default'), None)





        # create the application (FORWARD!)

        # Check if user supplied Owner information for the Application
        try:
            owner_id = str(event['ResourceProperties']['OwnerID'])
            owner_type = str(event['ResourceProperties']['OwnerType'])
        except KeyError:
            # If OwnerID or OwnerType is missing, use the current user
            # get the current user id
            response = http.request(
                'GET',
                'https://api.venafi.cloud/v1/useraccounts',
                headers={
                    'accept': 'application/json',
                    'tppl-api-key': api_key
                })
            owner_id = json.loads(response.data.decode('utf-8'))['user']['id']
            owner_type = "USER"

        print(f'Creating {application_name} in Venafi')
        data = {
            "name": application_name, 
            "ownerIdsAndTypes": [ 
                { 
                    "ownerId": user_id,
                    "ownerType": owner_type
                }
            ],
            "certificateIssuingTemplateAliasIdMap": {
                issuing_template_name: template_id
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
        # response = http.request(
        # 'GET',
        # f'https://api.venafi.cloud/outagedetection/v1/applications/name/{application_name}',
        # headers={
        #     'accept': 'application/json',
        #     'tppl-api-key': api_key
        # })

        # store response json data in a dictionary
      
        # app_guid = json.loads(response.data.decode('utf-8'))['id']
        # print(f'App GUID: {app_guid}')
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
            }
        )
      
        responseData = {}
        responseData['message'] = "Venafi application successfully deleted"
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)
    else:
        logging.error('Unknown operation: %s', event.get('RequestType'))