import os
import datetime
import traceback
import boto3

cloudformation = boto3.client('cloudformation')

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

def lambda_handler(event, context):
    stack_id = os.getenv("TARGET_STACK_ID")
    try:
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