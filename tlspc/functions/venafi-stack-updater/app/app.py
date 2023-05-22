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

def stack_marker_present(target_s3_bucket, stack_id):
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

# the stack marker logic is required because the AWS::Scheduler::Schedule fires its first event right at the point of creation
# this means the Create event is followed IMMEDIATELY by the first Update event and there's nothing developers can do to alter this.
# this is NOT the required behavior for certificate renewals so this logic, used whenever the AWS::Scheduler::Schedule resource fires, checks for the existence of an S3 object which represents the Stack (stack_marker_present())
# when this returns False, it knows this is the very first invocation for this Stack so it lays down a marker (write_stack_marker()) and skips the Update.
# Every subsequent invocation sees the marker, returns True, and commits to the cloudformation.update_stack() as normal.

def lambda_handler(event, context):
    target_s3_bucket = os.getenv("TARGET_S3_BUCKET")
    stack_id = os.getenv("STACK_ID")
    logger.info('event:\n' + json.dumps(event))
    logger.info('target_s3_bucket: ' + target_s3_bucket)
    logger.info('stack_id: ' + stack_id)
    try:
        if not stack_marker_present(target_s3_bucket, stack_id):
            write_stack_marker(target_s3_bucket, stack_id)
        else:
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