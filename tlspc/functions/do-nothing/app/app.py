import logging
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_handler(event, context):
    try:
        requestInfo = 'RequestType: Create'
        logger.info(requestInfo)
        ###########
        # code here
        ###########
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

def default_handler(event, context):
    try:
        requestInfo = 'RequestType: UNKNOWN'
        logger.info(requestInfo)
        ###########
        # code here
        ###########
    finally:
        responseData = {}
        responseData['message'] = requestInfo
        cfnresponse.send(event, context, cfnresponse.FAILED, responseData)

######
# main
######
def lambda_handler(event, context):
    logger.info('Received event: ' + str(event))

    requestTypeHandlers = {
        'Create': create_handler,
        'Update': update_handler,
        'Delete': delete_handler
    }
    
    requestTypeHandler = requestTypeHandlers.get(event.get('RequestType'), default_handler)
    requestTypeHandler(event, context)
