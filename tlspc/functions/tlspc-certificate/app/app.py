import logging
import time
from datetime import datetime
import json
import urllib3
import traceback
import cfnresponse
from vcert import (CertificateRequest, venafi_connection)
import boto3 # https://github.com/psf/requests/issues/6443 (requests==2.28.1)
import botocore

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

def get_aws_account():
    sts = boto3.client('sts')
    return sts.get_caller_identity().get('Account')

def get_aws_region():
    session = botocore.session.Session()
    return session.get_config_variable('region')

def get_parameters(event):
    api_key = str(event['ResourceProperties']['TLSPCAPIKey'])
    common_name = str(event['ResourceProperties']['CommonName'])
    zone = str(event['ResourceProperties']['Zone']) # e.g. 'my-app\\Default'
    target_s3_bucket = str(event['ResourceProperties'].get('TargetS3Bucket', ''))
    if not target_s3_bucket:
        target_s3_bucket = 'venafi-tlspc-certificates-' + get_aws_account()
    return api_key, common_name, zone, target_s3_bucket

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
    # NOTE PhysicalResourceId represents the first CR (which changes upon renewals!)
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
    max_attempts = 10
    for i in range(max_attempts):
        time.sleep(2)
        logger.info('retreive_cert_with_retry: attempt: '+ str(i))
        cert = conn.retrieve_cert(request)
        if cert is not None:
            return cert
    raise Exception(f"Function {function.__name__} failed after {max_attempts} attempts")

def get_cert_id(api_key, request_id):
    # the VCert SDK call to conn.retrieve_cert() works fine locally (via SAM) but once deployed into AWS the value for request.cert_guid was ALWAYS null ¯\_(ツ)_/¯
    response = http.request(
        'GET',
        'https://api.venafi.cloud/outagedetection/v1/certificaterequests/' + request_id,
        headers={
            'accept': 'application/json',
            'tppl-api-key': api_key
        })
    data = json.loads(response.data.decode('utf-8'))
    return data.get('certificateIds')[0]

def store_cert_in_s3(target_s3_bucket, physical_resource_id, cert):
    date_prefix = datetime.utcnow().strftime("%Y/%m/%d/%H/%M/%S/")
    latest_prefix = f'LATEST/{physical_resource_id}/'
    dated_prefix = f'{date_prefix}{physical_resource_id}/'    
    latest_key = f'{latest_prefix}cert.pem'
    dated_key = f'{dated_prefix}cert.pem'
    s3 = boto3.client('s3')
    s3.put_object(Body=cert.full_chain, Bucket=target_s3_bucket, Key=latest_key)
    s3.put_object(Body=cert.full_chain, Bucket=target_s3_bucket, Key=dated_key)
    aws_region = get_aws_region()
    return f'https://s3.console.aws.amazon.com/s3/buckets/{target_s3_bucket}?region={aws_region}&prefix={latest_key}', f'https://s3.console.aws.amazon.com/s3/buckets/{target_s3_bucket}?region={aws_region}&prefix={dated_key}'

def create_handler(event, context):
    responseData = {}
    requestInfo = 'RequestType: Create'
    logger.info(requestInfo)
    ###########
    # code here
    ###########
    api_key, common_name, zone, target_s3_bucket = get_parameters(event)
    conn = venafi_connection(api_key=api_key)
    request = CertificateRequest(common_name=common_name)
    conn.request_cert(request, zone)
    cert = retreive_cert_with_retry(conn, request)
    logger.info('certificate retrieved')

    s3_url_latest, s3_url_dated = store_cert_in_s3(target_s3_bucket, request.id, cert)
    logger.info('objects stored')
    ###########
    responseData['PhysicalResourceId'] = request.id
    responseData['LatestCertRequestId'] = request.id
    responseData['LatestCertId'] = request.cert_guid
    responseData['S3URLLatest'] = s3_url_latest
    responseData['S3URLDated'] = s3_url_dated
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
    api_key, _, _, target_s3_bucket = get_parameters(event)
    latest_cert_request_id = get_stack_output_value(event, 'LatestCertRequestId')
    conn = venafi_connection(api_key=api_key)

    request = CertificateRequest(cert_id=latest_cert_request_id)
    conn.renew_cert(request)
    cert_id = get_cert_id(api_key, request.id)
    logger.info('certificate renewed')

    # after conn.renew_cert, request.cert_guid is only set after a successful call to conn.retrieve_cert() ... unless you're in AWS! (see get_cert_id())
    cert = retreive_cert_with_retry(conn, request)
    cert_id = get_cert_id(api_key, request.id)
    logger.info('renewed certificate retrieved')

    s3_url_latest, s3_url_dated = store_cert_in_s3(target_s3_bucket, physical_resource_id, cert) # physical_resource_id used to ensure consistency with first CR (version history)
    logger.info('objects stored')
    ###########
    responseData['PhysicalResourceId'] = physical_resource_id # fix PhysicalResourceId to first CR, to CFN happy
    responseData['LatestCertRequestId'] = request.id
    responseData['LatestCertId'] = cert_id # should be able to use request.cert_guid, but ¯\_(ツ)_/¯
    responseData['S3URLLatest'] = s3_url_latest
    responseData['S3URLDated'] = s3_url_dated
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
    api_key, _, _, _ = get_parameters(event)
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
    logger.info('certificate retired - NOTE objects may remain in S3')
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
