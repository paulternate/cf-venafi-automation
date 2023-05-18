import os
import datetime
import traceback
import boto3

def lambda_handler(event, context):
    stack_id = os.getenv("TARGET_STACK_ID")
    cloudformation = boto3.client('cloudformation')
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    try:
        response = cloudformation.update_stack(
            StackName=stack_id,
            UsePreviousTemplate=True,
            Parameters=[
                {
                    'ParameterKey': 'TLSPCAPIKey',
                    'UsePreviousValue': True
                },
                {
                    'ParameterKey': 'UpdateTrigger',
                    'ParameterValue': timestamp
                }
            ]
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