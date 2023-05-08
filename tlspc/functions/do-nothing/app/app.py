import logging
import cfnresponse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def create_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Create'
    logger.info(requestInfo)
    ###########
    # code here
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
    responseData['message'] = requestInfo
    return responseData

def delete_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Delete'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    responseData['message'] = requestInfo
    return responseData

def lambda_handler_ex_cfn(event, context):
    logger.info('Received event: ' + str(event))
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
