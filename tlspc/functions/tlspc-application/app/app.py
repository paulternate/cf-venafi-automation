import logging
import json
import urllib3
import traceback
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

def get_parameters(event):
    api_key=(str(event['ResourceProperties']['TLSPCAPIKey']))
    app_name=(str(event['ResourceProperties']['AppName']))
    issuing_template_name=(str(event['ResourceProperties']['IssuingTemplateName']))
    cert_authority=(str(event['ResourceProperties']['CertificateAuthority']))
    return api_key,app_name,issuing_template_name,cert_authority

def get_physical_resource_id(event):
    physical_resource_id=(str(event.get('PhysicalResourceId', None)))
    return physical_resource_id

def get_template_id(api_key, issuing_template_name, cert_authority):
    logger.info('getting template_id')
    response = http.request(
        'GET',
        'https://api.venafi.cloud/v1/certificateissuingtemplates',
        headers={
            'accept': 'application/json',
            'tppl-api-key': api_key
        })
    template_id = next(
        (t['id'] for t in json.loads(response.data.decode('utf-8'))['certificateIssuingTemplates']
            if t['name'] == issuing_template_name and t['certificateAuthority'] == cert_authority),
        None
    )
    
    return template_id

def get_current_user_id(api_key):
    logger.info('getting owner_id')
    response = http.request(
        'GET',
        'https://api.venafi.cloud/v1/useraccounts',
        headers={
            'accept': 'application/json',
            'tppl-api-key': api_key
        })
    owner_id = json.loads(response.data.decode('utf-8'))['user']['id']
    return owner_id

def build_payload(app_name, issuing_template_name, owner_id, template_id):
    data = {
        "name": app_name,
        "ownerIdsAndTypes": [ 
            { 
                "ownerId": owner_id,
                "ownerType": "USER"
            }
        ],
        "certificateIssuingTemplateAliasIdMap": {
            issuing_template_name: template_id
        }
    }
    logger.info('payload:\n' + json.dumps(data))
    return data

def create_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Create'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    api_key, app_name, issuing_template_name, cert_authority = get_parameters(event)
    owner_id = get_current_user_id(api_key)
    template_id = get_template_id(api_key, issuing_template_name, cert_authority)
    payload = build_payload(app_name, issuing_template_name, owner_id, template_id)
    response = http.request(
        'POST',
        'https://api.venafi.cloud/outagedetection/v1/applications',
        headers={
            'accept': 'application/json',
            'content-type': 'application/json',
            'tppl-api-key': api_key
        },
        body=json.dumps(payload).encode('utf-8')
    )
    logger.info('response:\n' + json.dumps(response.data.decode('utf-8')))
    responseData['PhysicalResourceId'] = json.loads(response.data.decode('utf-8'))['applications'][0]['id']
    ###########
    responseData['Message'] = requestInfo
    return responseData

def update_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Update'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    physical_resource_id = get_physical_resource_id(event)
    api_key, app_name, issuing_template_name, cert_authority = get_parameters(event)
    owner_id = get_current_user_id(api_key)
    template_id = get_template_id(api_key, issuing_template_name, cert_authority)
    payload = build_payload(app_name, issuing_template_name, owner_id, template_id)
    logger.info('physical_resource_id:' + physical_resource_id)
    response = http.request(
        'PUT',
        'https://api.venafi.cloud/outagedetection/v1/applications/' + physical_resource_id,
        headers={
            'accept': 'application/json',
            'content-type': 'application/json',
            'tppl-api-key': api_key
        },
        body=json.dumps(payload).encode('utf-8')
    )
    logger.info('response:\n' + json.dumps(response.data.decode('utf-8')))
    responseData['PhysicalResourceId'] = physical_resource_id # failure to do this will trigger a delete
    ###########
    responseData['Message'] = requestInfo
    return responseData

def delete_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Delete'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    physical_resource_id = get_physical_resource_id(event)
    api_key, _, _, _ = get_parameters(event)
    logger.info('physical_resource_id:' + physical_resource_id)
    response = http.request(
        'DELETE',
        'https://api.venafi.cloud/outagedetection/v1/applications/' + physical_resource_id,
        headers={
            'accept': '*/*',
            'tppl-api-key': api_key
        }
    )
    logger.info('response:\n' + json.dumps(response.data.decode('utf-8')))
    responseData['PhysicalResourceId'] = physical_resource_id
    ###########
    responseData['Message'] = requestInfo
    return responseData

def lambda_handler_ex_cfn(event, context):
    logger.info('event:\n' + json.dumps(event))
    logger.info('context:\n' + str(context))
    requestTypeHandlers = {
        'Create': create_handler,
        'Update': update_handler,
        'Delete': delete_handler
    }
    requestTypeHandler = requestTypeHandlers.get(event.get('RequestType'))
    return requestTypeHandler(event, context)

def lambda_handler(event, context):
    responseData = {}
    responseStatus = cfnresponse.SUCCESS
    try:
        responseData = lambda_handler_ex_cfn(event, context)
    except Exception as e:
        responseStatus = cfnresponse.FAILED
        responseData['Message'] = traceback.format_exc()
    finally:
        cfnresponse.send(event, context, responseStatus, responseData, responseData.get('PhysicalResourceId', None))
