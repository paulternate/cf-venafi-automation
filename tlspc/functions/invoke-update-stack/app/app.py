import os
import json
import traceback
import boto3 # https://github.com/psf/requests/issues/6443 (requests==2.28.1)

def lambda_handler(event, context):
    stack_id = os.getenv("TARGET_STACK_ID")
    cloudformation = boto3.client('cloudformation')
    # response = cloudformation.describe_stacks(StackName=stack_id)
    # json_data = json.loads(response)
    # return json.dumps(json_data, indent=2)
    response = None
    try:
        response = cloudformation.describe_stacks(StackName=stack_id)
    except Exception as e:
        response = traceback.format_exc()
    finally:
        return response

def main():
    print(lambda_handler(None, None))

if __name__ == '__main__':
    main()