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
    app_description=(str(event['ResourceProperties']['AppDescription']))
    issuing_template_name=(str(event['ResourceProperties']['IssuingTemplateName']))
    cert_authority=(str(event['ResourceProperties']['CertificateAuthority']))
    return api_key, app_name, app_description, issuing_template_name, cert_authority

def redact_sensitive_info(json_data, sensitive_key, redacted_value='***'):
    data = json.loads(json_data)
    keys = sensitive_key.split('.')
    current = data
    for key in keys[:-1]:
        if key in current:
            current = current[key]
        else:
            return json_data
    if keys[-1] in current:
        current[keys[-1]] = redacted_value
    redacted_json = json.dumps(data)
    return redacted_json

def get_physical_resource_id(event):
    return (str(event.get('PhysicalResourceId', None)))

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

def build_payload(app_name, app_description, issuing_template_name, owner_id, template_id):
    data = {
        "name": app_name,
        "description": app_description,
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
    logger.info('RequestType: Create')
    ###########
    # code here
    ###########
    api_key, app_name, app_description, issuing_template_name, cert_authority = get_parameters(event)
    owner_id = get_current_user_id(api_key)
    template_id = get_template_id(api_key, issuing_template_name, cert_authority)
    payload = build_payload(app_name, app_description, issuing_template_name, owner_id, template_id)
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
    ###########
    responseData['PhysicalResourceId'] = json.loads(response.data.decode('utf-8'))['applications'][0]['id']
    responseData['IssuingTemplateId'] = template_id
    return responseData

def update_handler(event, context):
    responseData = {}
    logger.info('RequestType: Update')
    physical_resource_id = get_physical_resource_id(event)
    ###########
    # code here
    ###########
    api_key, app_name, app_description, issuing_template_name, cert_authority = get_parameters(event)
    owner_id = get_current_user_id(api_key)
    template_id = get_template_id(api_key, issuing_template_name, cert_authority)
    payload = build_payload(app_name, app_description, issuing_template_name, owner_id, template_id)
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
    ###########
    responseData['PhysicalResourceId'] = physical_resource_id # failure to do this will trigger a delete
    responseData['IssuingTemplateId'] = template_id
    return responseData

def delete_handler(event, context):
    responseData = {}
    logger.info('RequestType: Delete')
    physical_resource_id = get_physical_resource_id(event)
    ###########
    # code here
    ###########
    api_key, _, _, _, _ = get_parameters(event)
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
    ###########
    responseData['PhysicalResourceId'] = physical_resource_id
    return responseData

def lambda_handler(event, context):
    responseData = {}
    responseStatus = cfnresponse.SUCCESS
    try:
        logger.info('event:\n' + redact_sensitive_info(json.dumps(event), 'ResourceProperties.TLSPCAPIKey'))
        logger.info('context:\n' + str(context))
        requestTypeHandlers = {
            'Create': create_handler,
            'Update': update_handler,
            'Delete': delete_handler
        }
        requestTypeHandler = requestTypeHandlers.get(event.get('RequestType'))
        responseData = requestTypeHandler(event, context)
    except Exception as e:
        responseStatus = cfnresponse.FAILED
        responseData['Message'] = traceback.format_exc()
    finally:
        cfnresponse.send(event, context, responseStatus, responseData, responseData.get('PhysicalResourceId', None))
