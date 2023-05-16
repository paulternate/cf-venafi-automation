import logging
import time
import json
import urllib3
import traceback
import cfnresponse
from vcert import (CertificateRequest, venafi_connection)
import boto3 # https://github.com/psf/requests/issues/6443 (requests==2.28.1)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

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

def get_stack_outputs(event):
    stack_name = event['StackId']
    cloudformation = boto3.client('cloudformation')
    response = cloudformation.describe_stacks(StackName=stack_name)
    return response['Stacks'][0]['Outputs']

def get_stack_output_value(event, output_key):
    stack_outputs = get_stack_outputs(event)
    return next((o['OutputValue'] for o in stack_outputs if o['OutputKey'] == output_key), None)

def retreive_cert_with_retry(conn, request):
    max_attempts = 5
    for i in range(max_attempts):
        time.sleep(4)
        logger.info('retreive_cert_with_retry: attempt: '+ i)
        logger.info('request.cert_guid (before): ' + request.cert_guid)
        cert = conn.retrieve_cert(request)
        logger.info('request.cert_guid (after): ' + request.cert_guid)
        if cert is not None:
            return cert
    raise Exception(f"Function {function.__name__} failed after {max_attempts} attempts")

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
    cert = retreive_cert_with_retry(conn, request)
    logger.info('certificate retrieved')
    # TODO add the new cert to S3
    ###########
    responseData['PhysicalResourceId'] = request.id
    responseData['LatestCertRequestId'] = request.id
    responseData['LatestCertId'] = request.cert_guid
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
    latest_cert_request_id = get_stack_output_value(event, 'LatestCertRequestId')
    conn = venafi_connection(api_key=api_key)
    request = CertificateRequest(cert_id=latest_cert_request_id)
    conn.renew_cert(request)
    logger.info('certificate renewed')
    # after conn.renew_cert, request.cert_guid is only set after a successful call to conn.retrieve_cert()
    cert = retreive_cert_with_retry(conn, request)
    logger.info('renewed certificate retrieved')
    # TODO put the renewed cert in S3
    ###########
    responseData['PhysicalResourceId'] = physical_resource_id # fix PhysicalResourceId to first CR, to CFN happy
    responseData['LatestCertRequestId'] = request.id
    responseData['LatestCertId'] = request.cert_guid
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
    api_key, _, _ = get_parameters(event)
    latest_cert_id = get_stack_output_value(event, 'LatestCertId')
    logger.info('latest_cert_id: ' + latest_cert_id)
    payload = {
	    "addToBlocklist": True,
	    "certificateIds": [ latest_cert_id ]
    }
    response = http.request(
        'POST',
        'https://api.venafi.cloud/outagedetection/v1/certificates/retirement',
        headers={
            'accept': 'application/json',
            'content-type': 'application/json',
            'tppl-api-key': api_key
        },
        body=json.dumps(payload).encode('utf-8')
    )
    logger.info('certificate retired')
    # TODO remove revoked certificate from S3
    ###########
    responseData['PhysicalResourceId'] = physical_resource_id
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
