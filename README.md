# cf-venafi-automation

CloudFormation templates and accompanying files necessary for machine identity automation using the Venafi Control Plane.

## Tech Training 2023 - Venafi Ecosystem Workshop
The Venafi Ecosystem Workshop for Tech Training 2023 is accessible [here](docs/README.md)

## AWS CLI interface

```
TLSPCAPIKey=<API_KEY_FROM_TLSPC>
PrivateKeyPassphrase=<PRIVATE_KEY_PASSPHRASE>
STACK_BASE_NAME=elvispresley                  # <--- PERSONALIZE THIS TO SUIT

ID=${RANDOM}
ZONE=${STACK_BASE_NAME}-${ID}-app\\${STACK_BASE_NAME}-${ID}-cit
POLICY_STACK_NAME=${STACK_BASE_NAME}-${ID}-policy
CERT_STACK_NAME=${STACK_BASE_NAME}-${ID}-cert

# tlspc-policy
aws cloudformation create-stack \
  --stack-name ${POLICY_STACK_NAME} \
  --template-url https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-policy.yaml \
  --parameters \
    ParameterKey=Zone,ParameterValue=${ZONE} \
    ParameterKey=MaxValidDays,ParameterValue=91 \
    ParameterKey=TLSPCAPIKey,ParameterValue=${TLSPCAPIKey}

# tlspc-certificate (create)
aws cloudformation create-stack \
  --stack-name ${CERT_STACK_NAME} \
  --template-url https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-certificate.yaml \
  --parameters \
    ParameterKey=Zone,ParameterValue=${ZONE} \
    ParameterKey=CommonName,ParameterValue=www${RandomKey}.${STACK_BASE_NAME}.com \
    ParameterKey=ValidityHours,ParameterValue=0 \
    ParameterKey=RenewalHours,ParameterValue=1 \
    ParameterKey=TLSPCAPIKey,ParameterValue=${TLSPCAPIKey} \
    ParameterKey=PrivateKeyPassphrase,ParameterValue=${PrivateKeyPassphrase} \
    ParameterKey=TargetS3Bucket,ParameterValue= \
    ParameterKey=UpdateTrigger,ParameterValue=

# tlspc-certificate (update)
aws cloudformation update-stack \
  --stack-name ${CERT_STACK_NAME}-${RandomKey} \
  --use-previous-template \
  --parameters \
    ParameterKey=Zone,UsePreviousValue=true \
    ParameterKey=CommonName,UsePreviousValue=true \
    ParameterKey=ValidityHours,UsePreviousValue=true \
    ParameterKey=RenewalHours,UsePreviousValue=true \
    ParameterKey=TLSPCAPIKey,UsePreviousValue=true \
    ParameterKey=PrivateKeyPassphrase,UsePreviousValue=true \
    ParameterKey=TargetS3Bucket,UsePreviousValue=true \
    ParameterKey=UpdateTrigger,ParameterValue=$(uuidgen)
```
