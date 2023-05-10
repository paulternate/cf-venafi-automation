import logging
import json
import urllib3
import boto3
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

def get_template_id(api_key, issuing_template_name, cert_authority):
    logger.info("getting template_id")
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
    logger.info("getting owner_id")
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
    logger.info("api payload created: data=" + str(data))
    return data

def get_app_guid(event):
    stackId = event.get('StackId')
    logger.info('stackId=' + stackId)
    cfn_client = boto3.client('cloudformation')
    stacks = cfn_client.describe_stacks(StackName = stackId)
    logger.info('stacks=' + str(stacks))
    app_guid = next((output['OutputValue'] for output in stacks['Stacks'][0]['Outputs'] if output['OutputKey'] == 'AppGUID'), None)
    logger.info('app_guid=' + app_guid)
    return app_guid

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
    logger.info("response=" + str(response))
    responseData['AppGUID'] = json.loads(response.data.decode('utf-8'))['applications'][0]['id']
    ###########
    responseData['message'] = requestInfo
    return responseData

def update_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Update'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    app_guid = get_app_guid(event)
    api_key, app_name, issuing_template_name, cert_authority = get_parameters(event)   
    owner_id = get_current_user_id(api_key)
    template_id = get_template_id(api_key, issuing_template_name, cert_authority)
    payload = build_payload(app_name, issuing_template_name, owner_id, template_id)
    response = http.request(
        'PUT',
        'https://api.venafi.cloud/outagedetection/v1/applications/' + app_guid,
        headers={
            'accept': '*/*',
            'tppl-api-key': api_key
        },
        body=json.dumps(payload).encode('utf-8')
    )
    logger.info('response=' + str(response))
    ###########
    responseData['message'] = requestInfo
    return responseData

def delete_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Delete'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    app_guid = get_app_guid(event)
    api_key, _, _, _ = get_parameters(event)   
    response = http.request(
        'PUT',
        'https://api.venafi.cloud/outagedetection/v1/applications/' + app_guid,
        headers={
            'accept': '*/*',
            'tppl-api-key': api_key
        }
    )
    logger.info('response=' + str(response))
    ###########
    responseData['message'] = requestInfo
    return responseData

def lambda_handler_ex_cfn(event, context):
    logger.info('event=' + str(event) + ' context=' + str(context))
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
        responseData['message'] = str(e)
    finally:
        cfnresponse.send(event, context, responseStatus, responseData)
