import logging
import json
import traceback
import cfnresponse
from vcert import (CertificateRequest, venafi_connection)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_parameters(event):
    api_key=(str(event['ResourceProperties']['TLSPCAPIKey']))
    common_name=(str(event['ResourceProperties']['CommonName']))
    zone=(str(event['ResourceProperties']['Zone'])) # e.g. 'my-app\\Default'
    return api_key, common_name, zone

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
    # NOTE PhysicalResourceId represents the CR (which changes upon renewals!)
    physical_resource_id=(str(event.get('PhysicalResourceId', None)))
    return physical_resource_id

def create_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Create'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    api_key, common_name, zone = get_parameters(event)
    conn = venafi_connection(api_key=api_key)
    request = CertificateRequest(common_name=common_name)
    conn.request_cert(request, zone)
    cert = conn.retrieve_cert(request)
    logger.info('certificate retrieved')
    # TODO add the new cert to S3
    ###########
    responseData['PhysicalResourceId'] = request.id  
    responseData['CertGuid'] = request.cert_guid
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
    api_key, _, _ = get_parameters(event)
    conn = venafi_connection(api_key=api_key)
    request = CertificateRequest(cert_id=physical_resource_id) # <- this works, even though we appear to be mixing up certs and CRs
    conn.renew_cert(request)
    cert = conn.retrieve_cert(request)
    logger.info('certificate retrieved')
    # TODO put the renewed cert in S3
    ###########
    responseData['PhysicalResourceId'] = request.id # NOTE physical_resource_id is "old" at this point, so pull in updated value from the request
    responseData['CertGuid'] = request.cert_guid
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
    # plan - retiring the most recent cert removes the history from the UI
    # TODO delete the cert from S3
    ###########
    responseData['PhysicalResourceId'] = physical_resource_id
    responseData['CertGuid'] = request.cert_guid
    responseData['message'] = requestInfo
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
