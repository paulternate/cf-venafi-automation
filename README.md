# cf-venafi-automation

CloudFormation templates and accompanying files necessary for machine identity automation using the Venafi Control Plane.

## Venafi Ecosystem Workshop
The Venafi Ecosystem Workshop is accessible [here](docs/README.md)

## AWS CLI interface

```
TLSPCAPIKey=<API_KEY_FROM_TLSPC>
PrivateKeyPassphrase=<PRIVATE_KEY_PASSPHRASE>
STACK_BASE_NAME=elvispresley                  # <--- PERSONALIZE THIS TO SUIT

ID=${RANDOM} # a "random" number to introduce uniqueness and avoid collisions
ZONE=${STACK_BASE_NAME}-${ID}-app\\${STACK_BASE_NAME}-${ID}-cit

# tlspc-policy (create)
aws cloudformation create-stack \
  --stack-name ${STACK_BASE_NAME}-${ID}-policy \
  --template-url https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-policy.yaml \
  --parameters \
    ParameterKey=CertificateAuthority,ParameterValue="Built-In CA" \
    ParameterKey=Zone,ParameterValue=${ZONE} \
    ParameterKey=MaxValidDays,ParameterValue=91 \
    ParameterKey=Domains,ParameterValue=\"${STACK_BASE_NAME}.com,example.com\" \
    ParameterKey=TLSPCAPIKey,ParameterValue=${TLSPCAPIKey}

# # tlspc-policy (update)
#   awaiting fix ...
# aws cloudformation update-stack \
#   --stack-name ${STACK_BASE_NAME}-${ID}-policy \
#   --template-url https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-policy.yaml \
#   --parameters \
#     ParameterKey=CertificateAuthority,UsePreviousValue=true \
#     ParameterKey=Zone,UsePreviousValue=true \
#     ParameterKey=MaxValidDays,ParameterValue=92 \
#     ParameterKey=Domains,UsePreviousValue=true \
#     ParameterKey=TLSPCAPIKey,UsePreviousValue=true

# tlspc-certificate (create)
aws cloudformation create-stack \
  --stack-name ${STACK_BASE_NAME}-${ID}-cert \
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
  --stack-name ${STACK_BASE_NAME}-${ID}-cert \
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
