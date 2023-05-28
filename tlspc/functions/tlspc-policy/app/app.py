import logging
import json
import traceback
import cfnresponse
import urllib3
import http
from vcert import venafi_connection
from vcert.policy.policy_spec import (PolicySpecification, Policy, Defaults)

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
    physical_resource_id=(str(event.get('PhysicalResourceId', None)))
    return physical_resource_id

def get_parameters(event):
    api_key = str(event['ResourceProperties']['TLSPCAPIKey'])
    zone = str(event['ResourceProperties']['Zone'])
    return api_key, zone

def create_handler(event, context):
    responseData = {}
    logger.info('RequestType: Create')
    ###########
    # code here
    ###########
    api_key, zone = get_parameters(event)
    connector = venafi_connection(api_key=api_key)
    ps = PolicySpecification()
    ps.policy = Policy()
    ps.defaults = Defaults()
    connector.set_policy(zone, ps)
    response = connector.get_policy(zone)
    ###########
    responseData['PhysicalResourceId'] = zone
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
