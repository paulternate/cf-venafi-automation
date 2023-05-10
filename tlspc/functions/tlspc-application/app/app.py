import logging
import json
import urllib3
import cfnresponse
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

def create_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Create'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    api_key=(str(event['ResourceProperties']['TLSPCAPIKey']))
    app_name=(str(event['ResourceProperties']['AppName']))
    issuing_template_name=(str(event['ResourceProperties']['IssuingTemplateName']))
    cert_authority=(str(event['ResourceProperties']['CertificateAuthority']))    
    logger.info("getting owner_id")
    response = http.request(
        'GET',
        'https://api.venafi.cloud/v1/useraccounts',
        headers={
            'accept': 'application/json',
            'tppl-api-key': api_key
        })
    owner_id = json.loads(response.data.decode('utf-8'))['user']['id']
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
    logger.info("Create: response=" + str(response))
    responseData['appGUID'] = json.loads(response.data.decode('utf-8'))['applications'][0]['id']
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
    # TBD needs a PUT request on https://api.venafi.cloud/outagedetection/v1/applications/<APP_GUID>
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
    client = boto3.client('cloudformation')
    stackId = event.get('StackId')
    logger.info('stackName=' + stackId)
    response = client.describe_stacks(StackName = stackId)
    appGUID = next((output['OutputValue'] for output in response['Stacks'][0]['Outputs'] if output['OutputKey'] == 'appGUID'), None)
    logger.info('appGUID=' + appGUID)
    response = http.request(
        'DELETE',
        'https://api.venafi.cloud/outagedetection/v1/applications/' + appGUID,
        headers={
            'accept': '*/*',
            'tppl-api-key': api_key
        }
    )
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
