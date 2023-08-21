import logging
import time
import json
import urllib3
import traceback
import cfnresponse
from vcert import (CertificateRequest, venafi_connection, CSR_ORIGIN_SERVICE)
import boto3
import botocore
from botocore.exceptions import ClientError
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

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
    validity_hours = None if int(event['ResourceProperties']['ValidityHours']) == 0 else int(event['ResourceProperties']['ValidityHours'])
    private_key_passphrase = str(event['ResourceProperties']['PrivateKeyPassphrase'])
    target_s3_bucket = str(event['ResourceProperties']['TargetS3Bucket'])
    if not target_s3_bucket:
        target_s3_bucket = 'venafi-tlspc-certificates-' + get_aws_account()
    publish_to_acm = str(event['ResourceProperties']['PublishToACM'])
    return api_key, common_name, zone, validity_hours, private_key_passphrase, target_s3_bucket, publish_to_acm

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
    # NOTE In this Function, PhysicalResourceId represents the very first CR in its series so it NEVER changes (a requirement for CFN to behave as expected)
    return (str(event.get('PhysicalResourceId', None)))

def get_stack_outputs(event):
    stack_id = event['StackId']
    cloudformation = boto3.client('cloudformation')
    response = cloudformation.describe_stacks(StackName=stack_id)
    outputs = response['Stacks'][0]['Outputs']
    logger.info('stack_outputs:\n' + json.dumps(outputs))
    return outputs

def get_stack_output_value(event, output_key):
    try:
        stack_outputs = get_stack_outputs(event)
        return next((o['OutputValue'] for o in stack_outputs if o['OutputKey'] == output_key), None)
    except:
        return None

def retrieve_cert_with_retry(conn, request):
    timeout = 720 # 12 mins (Lambda itself has a hard limit at 15 mins)
    interval = 15
    start_time = time.time()
    attempt = 0
    cert = None
    while True:
        try:
            attempt += 1
            logger.info(f'retrieve_cert_with_retry() - attempt {attempt}')
            cert = conn.retrieve_cert(request)
            if cert is not None:
                break
        except Exception as e:
            logger.info(f'retrieve_cert_with_retry() - attempt {attempt} failed with exception: {str(e)}')

        elapsed_time = time.time() - start_time
        if elapsed_time >= timeout:
            break
        
        time.sleep(interval)
        
    if cert is None:
        raise Exception('retrieve_cert_with_retry() - failed to retrieve cert within {timeout} seconds.')
    
    return cert

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

def get_cert_expiry(api_key, cert_id):
    response = http.request(
        'GET',
        'https://api.venafi.cloud/outagedetection/v1/certificates/' + cert_id,
        headers={
            'accept': 'application/json',
            'tppl-api-key': api_key
        })
    data = json.loads(response.data.decode('utf-8'))
    return str(data.get('validityEnd'))[:19] # only use the first 19 chars, as the rest are zeros.

def store_cert_in_s3(target_s3_bucket, physical_resource_id, common_name, cert, stack_id, cert_request_id):
    object_prefix = f'certs/{common_name}/{physical_resource_id}/'
    s3 = boto3.client('s3')
    tags = [
        {'Key': 'StackId', 'Value': stack_id},
        {'Key': 'CertRequestId', 'Value': cert_request_id}
    ]
    s3.put_object(Bucket=target_s3_bucket, Key=f'{object_prefix}{common_name}.chain', Body=cert.full_chain)
    s3.put_object_tagging(Bucket=target_s3_bucket, Key=f'{object_prefix}{common_name}.chain', Tagging={'TagSet': tags})
    s3.put_object(Bucket=target_s3_bucket, Key=f'{object_prefix}{common_name}.cert', Body=cert.cert)
    s3.put_object_tagging(Bucket=target_s3_bucket, Key=f'{object_prefix}{common_name}.cert', Tagging={'TagSet': tags})
    s3.put_object(Bucket=target_s3_bucket, Key=f'{object_prefix}{common_name}.key', Body=cert.key)
    s3.put_object_tagging(Bucket=target_s3_bucket, Key=f'{object_prefix}{common_name}.key', Tagging={'TagSet': tags})
    logger.info(f'successfully stored and tagged key material objects in s3: target_s3_bucket={target_s3_bucket} object_prefix={object_prefix} common_name={common_name}')
    aws_region = get_aws_region()
    return f'https://s3.console.aws.amazon.com/s3/buckets/{target_s3_bucket}?region={aws_region}&prefix={object_prefix}'

def get_shortened_stack_id(stack_id):
    return stack_id.split('/', 1)[1]

def get_latest_cert_request_id_s3(target_s3_bucket, event):
    try:
        object_prefix = 'stacks/'
        stack_id = event['StackId']
        shortened_stack_id = get_shortened_stack_id(stack_id)
        s3 = boto3.client('s3')
        response = s3.get_object(Bucket=target_s3_bucket, Key=f'{object_prefix}{shortened_stack_id}/latest-cert-request-id.txt')
        request_id = response['Body'].read().decode('utf-8')
        logger.info(f'latest_cert_request_id objects read from s3: target_s3_bucket={target_s3_bucket} object_prefix={object_prefix} request_id={request_id}')
        return request_id
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return None
        else:
            raise

def set_latest_cert_request_id_s3(target_s3_bucket, event, request_id):
    object_prefix = 'stacks/'
    stack_id = event['StackId']
    shortened_stack_id = get_shortened_stack_id(stack_id)
    s3 = boto3.client('s3')
    s3.put_object(Bucket=target_s3_bucket, Key=f'{object_prefix}{shortened_stack_id}/latest-cert-request-id.txt', Body=request_id)
    logger.info(f'latest_cert_request_id objects saved to s3: target_s3_bucket={target_s3_bucket} object_prefix={object_prefix} request_id={request_id}')


def get_latest_cert_request_id(target_s3_bucket, event):
    value_from_outputs = get_stack_output_value(event, 'LatestCertRequestId')
    value_from_s3 = get_latest_cert_request_id_s3(target_s3_bucket, event)
    if (value_from_outputs or "") != (value_from_s3 or ""):
        # This situation indicates that the previous Stack Update resulted in failure.
        # This can happen when TLSPC fails to retrieve a certificate within 12 minutes of its renewal.
        # This results in the Stack Update being rolled back (standard CFN behaviour we're powerless to adjust)
        # When this happens it reverts the Stack Output for LatestCertRequestId to an OLD/INVALID value which thereafter causes incessant Stack Update failures.
        # The error is: "20908: Only existing certificate with CURRENT version can be specified. OLD versions are not supported".
        # The value_from_s3 is more resilient than the Stack Output for LatestCertRequestId and avoids this fate, so value_from_s3 now takes precedent.
        # The 20908 error is (hopefully) now avoided, but it's still worth logging ... for nostalgia? ;)
        logger.info(f'previous cert request ids do not match (continuing): value_from_outputs={value_from_outputs} value_from_s3={value_from_s3}')
    return value_from_s3 if value_from_s3 is not None else value_from_outputs

def decrypt_private_key(encrypted_key_content, private_key_passphrase):
    key = serialization.load_pem_private_key(
        encrypted_key_content.encode('utf-8'),
        password=private_key_passphrase.encode('utf-8'),
        backend=default_backend()
    )
    key_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    key_text = key_pem.decode('utf-8')
    return key_text

def import_cert_into_acm(cert, private_key_passphrase, reimport_arn=None):
    logger.info(f'importing key material into ACM')
    acm = boto3.client('acm')
    
    response = None
    if reimport_arn is None:
        # IMPORT (CertificateArn omitted)
        response = acm.import_certificate(
            CertificateChain=cert.full_chain,
            Certificate=cert.cert,
            PrivateKey=decrypt_private_key(cert.key, private_key_passphrase)
        )
    else:
        # RE-IMPORT
        response = acm.import_certificate(
            CertificateChain=cert.full_chain,
            Certificate=cert.cert,
            PrivateKey=decrypt_private_key(cert.key, private_key_passphrase),
            CertificateArn=reimport_arn
        )
    arn = response['CertificateArn']
    logger.info(f'successfully imported key material into ACM: ARN={arn}')
    aws_region = get_aws_region()
    cert_uid = arn[arn.rfind('/') + 1:]
    return f'https://{aws_region}.console.aws.amazon.com/acm/home?#/certificates/{cert_uid}'

def create_handler(event, context):
    responseData = {}
    logger.info('RequestType: Create')
    ###########
    # code here
    ###########
    api_key, common_name, zone, validity_hours, private_key_passphrase, target_s3_bucket, publish_to_acm = get_parameters(event)
    conn = venafi_connection(api_key=api_key)
    request = CertificateRequest(common_name=common_name)
    request.validity_hours = validity_hours
    request.csr_origin = CSR_ORIGIN_SERVICE
    request.key_password = private_key_passphrase
    # ---------------------------------------------
    # TODO Digicert sometimes fails with the following error so perhaps we need some retry logic here like we do in retrieve_cert_with_retry
    # File \"/var/task/vcert/connection_cloud.py\", line 406, in request_cert\n    request.cert_guid = data['certificateRequests'][0]['certificateIds'][0]\nIndexError: list index out of range\n"}}
    conn.request_cert(request, zone)
    # ---------------------------------------------
    set_latest_cert_request_id_s3(target_s3_bucket, event, request.id) # important to record this in case next steps fail/timeout
    cert = retrieve_cert_with_retry(conn, request)
    cert_expiry = get_cert_expiry(api_key, request.cert_guid)
    logger.info(f'certificate retrieved: request.id={request.id} request.cert_guid={request.cert_guid} cert_expiry={cert_expiry}')

    s3_url = store_cert_in_s3(target_s3_bucket, request.id, common_name, cert, event['StackId'], request.id)    
    acm_url, acm_arn = None, None
    if publish_to_acm != 'false':
        acm_url, acm_arn  = import_cert_into_acm(cert, private_key_passphrase)
    
    ###########
    responseData['PhysicalResourceId'] = request.id
    responseData['LatestCertRequestId'] = request.id
    responseData['LatestCertId'] = request.cert_guid
    responseData['LatestCertExpiry'] = cert_expiry
    responseData['TargetS3Bucket'] = target_s3_bucket
    responseData['S3URL'] = s3_url
    responseData['ACMURL'] = acm_url
    responseData['ACMARN'] = acm_arn
    return responseData

def update_handler(event, context):
    responseData = {}
    logger.info('RequestType: Update')
    physical_resource_id = get_physical_resource_id(event)
    ###########
    # code here
    ###########
    api_key, common_name, _, _, private_key_passphrase, target_s3_bucket, publish_to_acm = get_parameters(event)
    latest_cert_request_id = get_latest_cert_request_id(target_s3_bucket, event)
    conn = venafi_connection(api_key=api_key)

    request = CertificateRequest(cert_id=latest_cert_request_id)
    conn.renew_cert(request)
    set_latest_cert_request_id_s3(target_s3_bucket, event, request.id) # important to record this in case next steps fail/timeout
    cert_id = get_cert_id(api_key, request.id)
    logger.info(f'certificate renewed: request.id={request.id} cert_id={cert_id}')

    # after conn.renew_cert, request.cert_guid is only set after a successful call to conn.retrieve_cert() ... unless you're in AWS! (see get_cert_id())
    cert = retrieve_cert_with_retry(conn, request)
    cert_id = get_cert_id(api_key, request.id)
    cert_expiry = get_cert_expiry(api_key, cert_id)
    logger.info(f'renewed certificate retrieved: request.id={request.id} cert_id={cert_id} cert_expiry={cert_expiry}')

    s3_url = store_cert_in_s3(target_s3_bucket, physical_resource_id, common_name, cert, event['StackId'], request.id) # physical_resource_id used to ensure consistency with first CR (version history)
    acm_url, acm_arn = None, None
    if publish_to_acm != 'false':
        reimport_arn = get_stack_output_value(event, 'ACMARN')
        acm_url, acm_arn = import_cert_into_acm(cert, private_key_passphrase, reimport_arn)
    
    ###########
    responseData['PhysicalResourceId'] = physical_resource_id # fix PhysicalResourceId to first CR, to keep CFN happy
    responseData['LatestCertRequestId'] = request.id
    responseData['LatestCertId'] = cert_id # should be able to use request.cert_guid, but ¯\_(ツ)_/¯
    responseData['LatestCertExpiry'] = cert_expiry
    responseData['TargetS3Bucket'] = target_s3_bucket
    responseData['S3URL'] = s3_url
    responseData['ACMURL'] = acm_url
    responseData['ACMARN'] = acm_arn
    return responseData

def delete_handler(event, context):
    responseData = {}
    logger.info('RequestType: Delete')
    physical_resource_id = get_physical_resource_id(event)
    ###########
    # code here
    ###########
    api_key, _, _, _, _, _, _ = get_parameters(event)
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
    return responseData

def lambda_handler(event, context):
    responseData = {}
    responseStatus = cfnresponse.SUCCESS
    try:
        event_json=redact_sensitive_info(json.dumps(event), 'ResourceProperties.TLSPCAPIKey')
        event_json=redact_sensitive_info(event_json, 'ResourceProperties.PrivateKeyPassphrase')
        logger.info('event:\n' + event_json)
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
        responseData['Error'] = traceback.format_exc()
    finally:
        cfnresponse.send(event, context, responseStatus, responseData, responseData.get('PhysicalResourceId', None))
