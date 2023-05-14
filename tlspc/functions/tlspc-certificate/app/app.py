import logging
import json
import traceback
import cfnresponse
from vcert import (CertificateRequest, venafi_connection)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_parameters(event):
    api_key=(str(event['ResourceProperties']['TLSPCAPIKey']))
    zone=(str(event['ResourceProperties']['Zone'])) # e.g. 'my-app\\Default'
    common_name=(str(event['ResourceProperties']['CommonName']))
    return api_key, zone, common_name

def get_physical_resource_id(event):
    physical_resource_id=(str(event.get('PhysicalResourceId', None)))
    return physical_resource_id

def create_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Create'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    api_key, zone, common_name = get_parameters(event)
    conn = venafi_connection(api_key=api_key)
    request = CertificateRequest(common_name=common_name)
    conn.request_cert(request, zone)
    cert = conn.retrieve_cert(request)
    logger.info(cert.full_chain)
    ###########
    responseData['PhysicalResourceId'] = request.cert_guid
    responseData['message'] = requestInfo
    return responseData

def update_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Update'
    logger.info(requestInfo)
    physical_resource_id = get_physical_resource_id(event)
    ###########
    # code here
    ###########
    ###########
    responseData['PhysicalResourceId'] = physical_resource_id # failure to do this will trigger a delete
    responseData['message'] = requestInfo
    return responseData

def delete_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Delete'
    logger.info(requestInfo)
    physical_resource_id = get_physical_resource_id(event)
    ###########
    # code here
    ###########
    ###########
    responseData['PhysicalResourceId'] = physical_resource_id
    responseData['message'] = requestInfo
    return responseData

def lambda_handler(event, context):
    responseData = {}
    responseStatus = cfnresponse.SUCCESS
    try:
        # logger.info('event:\n' + json.dumps(event)) # <-- includes sensitive info!!!
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

