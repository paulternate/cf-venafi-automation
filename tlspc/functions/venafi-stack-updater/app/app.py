import logging
import json
import os
import datetime
import traceback
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)
cloudformation = boto3.client('cloudformation')
s3 = boto3.client('s3')

def get_stack_parameter_keys(stack_id):
    response = cloudformation.describe_stacks(StackName=stack_id)
    parameters = response['Stacks'][0]['Parameters']
    parameter_keys = [item['ParameterKey'] for item in parameters]
    return parameter_keys

def build_update_parameters(stack_id):
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    parameter_keys = get_stack_parameter_keys(stack_id)
    update_parameters = []
    for parameter_key in parameter_keys:
        if parameter_key == 'UpdateTrigger':
            update_parameters.append({
                    'ParameterKey': 'UpdateTrigger',
                    'ParameterValue': timestamp
                })
        else:
            update_parameters.append({
                    'ParameterKey': parameter_key,
                    'UsePreviousValue': True
                })
    return update_parameters

def wait_for_stack_create_complete(stack_id):
    # Outputs are not set until after Stack has completed
    response = cloudformation.describe_stacks(StackName=stack_id)
    stack_status = response['Stacks'][0]['StackStatus']
    if stack_status == 'CREATE_IN_PROGRESS':
        logger.info('waiting for stack creation to complete ...')
        waiter = cloudformation.get_waiter("stack_create_complete")
        waiter.wait(stack_id)

def is_stack_marker_present(target_s3_bucket, stack_id):
    try:
        object_prefix = 'stacks/'
        s3.head_object(Bucket=target_s3_bucket, Key=f'{object_prefix}{stack_id}.txt')
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        else:
            raise
    return True

def write_stack_marker(target_s3_bucket, stack_id):
    object_prefix = f'stacks/'
    s3.put_object(Bucket=target_s3_bucket, Key=f'{object_prefix}{stack_id}.txt', Body='for system usage, do not delete')

def get_stack_outputs(stack_id):
    response = cloudformation.describe_stacks(StackName=stack_id)
    return response['Stacks'][0]['Outputs']

def get_stack_output_value(stack_id, output_key):
    wait_for_stack_create_complete(stack_id)
    stack_outputs = get_stack_outputs(stack_id)
    return next((o['OutputValue'] for o in stack_outputs if o['OutputKey'] == output_key), None)

# the stack marker logic is required because the AWS::Scheduler::Schedule fires its first event right at the point of creation
# this means the Create event is followed IMMEDIATELY by the first Update event and there's nothing developers can do to alter this.
# this is NOT the required behavior for certificate renewals so this logic, used whenever the AWS::Scheduler::Schedule resource fires, checks for the existence of an S3 object which represents the Stack (stack_marker_present())
# when this returns False, it knows this is the very first invocation for this Stack so it lays down a marker (write_stack_marker()) and skips the Update.
# Every subsequent invocation sees the marker, returns True, and commits to the cloudformation.update_stack() as normal.

def lambda_handler(event, context):
    stack_id = os.getenv("STACK_ID")
    target_s3_bucket = get_stack_output_value(stack_id, 'TargetS3Bucket')
    logger.info('event:\n' + json.dumps(event))
    logger.info('target_s3_bucket: ' + target_s3_bucket)
    logger.info('stack_id: ' + stack_id)
    try:
        if not is_stack_marker_present(target_s3_bucket, stack_id):
            logger.info('first invocation being skipped')
            write_stack_marker(target_s3_bucket, stack_id)
        else:
            logger.info('subsequent invocation being processed normally')
            update_parameters = build_update_parameters(stack_id)
            response = cloudformation.update_stack(
                StackName=stack_id,
                UsePreviousTemplate=True,
                Parameters=update_parameters
            )
            response = None
    except Exception as e:
        response = traceback.format_exc()
    finally:
        return response

def main():
    print(lambda_handler(None, None))

if __name__ == '__main__':
    main()