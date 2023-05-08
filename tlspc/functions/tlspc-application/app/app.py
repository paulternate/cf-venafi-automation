import logging
import json
import urllib3
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

def create_handler(event, context):
    try:
        api_key=(str(event['ResourceProperties']['TLSPCAPIKey']))
        app_name = 'alan-test'
        user_id = 1
        owner_type = 'USER'
        issuing_template_name = 'a'
        template_id = 1

        requestInfo = 'RequestType: Create'
        logger.info(requestInfo)
        ###########
        # code here
        ###########
        data = {
            "name": app_name, 
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
        logger.info("Create: payload data=" + str(data))
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

    finally:
        responseData = {}
        responseData['message'] = requestInfo
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)

def update_handler(event, context):
    try:
        requestInfo = 'RequestType: Update'
        logger.info(requestInfo)
        ###########
        # code here
        ###########
    finally:
        responseData = {}
        responseData['message'] = requestInfo
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)

def delete_handler(event, context):
    try:
        requestInfo = 'RequestType: Delete'
        logger.info(requestInfo)
        ###########
        # code here
        ###########
    finally:
        responseData = {}
        responseData['message'] = requestInfo
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)

######
# main
######
def lambda_handler(event, context):
    try:
        logger.info('Received event: ' + str(event))
        requestTypeHandlers = {
            'Create': create_handler,
            'Update': update_handler,
            'Delete': delete_handler
        }
        requestTypeHandler = requestTypeHandlers.get(event.get('RequestType'))
        requestTypeHandler(event, context)
    except Exception as e:
        logger.error(str(e))
        responseData = {}
        responseData['message'] = str(e)
        cfnresponse.send(event, context, cfnresponse.FAILED, responseData)
    finally:
        logger.info('Completing lambda_handler')

