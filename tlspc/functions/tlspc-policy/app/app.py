import logging
import json
import traceback
import cfnresponse
import urllib3
import http
from vcert import venafi_connection
from vcert.policy.policy_spec import (PolicySpecification, Policy, Defaults)
from vcert.parser.utils import parse_policy_spec
import boto3
from pprint import pformat

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

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

def get_parameter(event, resource_property_key):
    return event['ResourceProperties'][resource_property_key]

def get_api_key(event):
    return str(get_parameter(event, 'TLSPCAPIKey'))

def get_zone(event):
    return str(get_parameter(event, 'Zone'))

def parse_zone(zone):
    segments = zone.split("\\")
    return segments[0], segments[1] # app_name, cit_alias

def get_cit_id(api_key, cit_alias):
    logger.info('getting cit_id')
    response = http.request(
        'GET',
        'https://api.venafi.cloud/v1/certificateissuingtemplates',
        headers={
            'accept': 'application/json',
            'tppl-api-key': api_key
        })
    cit_id = next(
        (t['id'] for t in json.loads(response.data.decode('utf-8'))['certificateIssuingTemplates']
            if t['name'] == cit_alias),
        None
    )
    return cit_id

def get_app_id(api_key, app_name):
    logger.info('getting app_id')
    response = http.request(
        'GET',
        'https://api.venafi.cloud/outagedetection/v1/applications',
        headers={
            'accept': 'application/json',
            'tppl-api-key': api_key
        })
    app_id = next(
        (t['id'] for t in json.loads(response.data.decode('utf-8'))['applications']
            if t['name'] == app_name),
        None
    )
    return app_id

def build_policy_spec(event):
    max_valid_days = int(get_parameter(event, 'MaxValidDays'))
    domains = str(get_parameter(event, 'Domains'))
    
    domains_array = [d.strip() for d in domains.split(',') if d]
    
    policy_spec = PolicySpecification()
    policy_spec.policy = Policy(
        max_valid_days = max_valid_days if max_valid_days != 0 else None,
        domains = domains_array
    )
    policy_spec.defaults = Defaults()
    return policy_spec

def create_handler(event, context):
    responseData = {}
    logger.info('RequestType: Create')
    ###########
    # code here
    ###########
    api_key = get_api_key(event)
    zone = get_zone(event)
    policy_spec = build_policy_spec(event)
    connector = venafi_connection(api_key=api_key)
    connector.set_policy(zone, policy_spec)
    app_name, cit_alias = parse_zone(zone)
    cit_id = get_cit_id(api_key, cit_alias)
    app_id = get_app_id(api_key, app_name)
    response = connector.get_policy(zone)
    policy_spec_data = pformat(parse_policy_spec(response))
    logger.info(f'Created/Updated Issuing Template: cit_id={cit_id} policy_spec_data:\n{policy_spec_data}')
    ###########
    responseData['PhysicalResourceId'] = cit_id # "TLSPCPolicy" resource is represented by the CertificateIssuingTemplate itself
    responseData['CertificateIssuingTemplateId'] = cit_id
    responseData['ApplicationId'] = app_id
    responseData['CertificateIssuingTemplatePolicy'] = policy_spec_data
    return responseData

def update_handler(event, context):
    responseData = {}
    logger.info('RequestType: Update')
    physical_resource_id = get_physical_resource_id(event)
    ###########
    # code here
    ###########

    ###########
    responseData['PhysicalResourceId'] = physical_resource_id # failure to do this will trigger a delete
    return responseData

def delete_handler(event, context):
    responseData = {}
    logger.info('RequestType: Delete')
    physical_resource_id = get_physical_resource_id(event)
    ###########
    # code here
    ###########
    # application first, then issuing template (best effort, swallow all errors)
    application_id = get_stack_output_value(event, 'ApplicationId')
    api_key = get_api_key(event)
    response = None
    try:
        response= http.request(
            'DELETE',
            f'https://api.venafi.cloud/outagedetection/v1/applications/{application_id}',
            headers={
                'accept': '*/*',
                'tppl-api-key': api_key
            }
        )
    except Exception as e:
        logger.info(f'delete_handler() - continuing after failed app deletion attempt: application_id={application_id} response={response}')

    try:
        response= http.request(
            'DELETE',
            f'https://api.venafi.cloud/v1/certificateissuingtemplates/{physical_resource_id}',
            headers={
                'accept': '*/*',
                'tppl-api-key': api_key
            }
        )
    except Exception as e:
        logger.info(f'delete_handler() - continuing after failed policy deletion attempt: physical_resource_id={physical_resource_id} response={response}')

    ###########
    responseData['PhysicalResourceId'] = physical_resource_id
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
        responseData['Error'] = traceback.format_exc()
    finally:
        cfnresponse.send(event, context, responseStatus, responseData, responseData.get('PhysicalResourceId', None))
