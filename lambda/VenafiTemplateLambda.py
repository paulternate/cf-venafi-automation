import cfnresponse
import json
import urllib3
import logging
import requests

logger = logging.getLogger()
logger.setLevel(logging.INFO)
http = urllib3.PoolManager()

def lambda_handler(event, context):
    logger.info('Received event: ' + str(event))
    api_key=(str(event['ResourceProperties']['TLSPCAPIKey']))
    template_policy_url=(str(event['ResourceProperties']['TemplatePolicyUrl']))

    if event.get('RequestType') == 'Create':

        # Set $body to the JSON at the remote template_policy_url
        response = requests.get(template_policy_url)
        if response.status_code == 200:
            request_body = json.loads(response.data)
        else:
            print(f"Error fetching JSON from {template_policy_url}: {response.status_code}")
        
        issuing_template_name = request_body['name']

        # Create Issuing Template in TLS Protect Cloud
        print(f'Creating {issuing_template_name} in TLS Protect Cloud')
        response = http.request(
            'POST',
            f'https://api.venafi.cloud/v1/certificateissuingtemplates',
            headers={
                'accept': 'application/json',
                'tppl-api-key': api_key
            },
            body=request_body         
            )
        
        issuing_template_id = json.loads(response.data.decode('utf-8'))['certificateIssuingTemplates'][0]['id']

        responseData = {}
        responseData['message'] = "Template created successfully"
        responseData['issuing_template_id'] = issuing_template_id
        responseData['issuing_template_name'] = issuing_template_name
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)

    elif event.get('RequestType') == 'Delete':
        print(f'Deleting {issuing_template_name} in TLS Protect Cloud')
        response = http.request(
            'DELETE',
            f'https://api.venafi.cloud/v1/certificateissuingtemplates/{issuing_template_id}',
            headers={
                'accept': 'application/json',
                'tppl-api-key': api_key
            })
        responseData = {}
        responseData['message'] = "Venafi Issuing Template successfully deleted"
        cfnresponse.send(event, context, cfnresponse.SUCCESS, responseData)

    else:
        logging.error('Unknown operation: %s', event.get('RequestType'))