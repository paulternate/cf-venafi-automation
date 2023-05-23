# cf-venafi-automation

CloudFormation templates and accompanying files necessary for machine identity automation using the Venafi Control Plane.

## Tech Training 2023 - Venafi Ecosystem Workshop
The Venafi Ecosystem Workshop for Tech Training 2023 is accessible [here](docs/README.md)

## AWS CLI interface

```
TLSPCAPIKey=<API_KEY_FROM_TLSPC>
PrivateKeyPassphrase=<PRIVATE_KEY_PASSPHRASE>
STACK_BASE_NAME=elvispresley                  # <--- PERSONALIZE THIS TO SUIT

APP_STACK_NAME=${STACK_BASE_NAME}-app
CERT_STACK_NAME=${STACK_BASE_NAME}-cert

# tlspc-application
aws cloudformation create-stack \
  --stack-name ${APP_STACK_NAME} \
  --template-url https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-application.yaml \
  --parameters \
    ParameterKey=AppName,ParameterValue=${APP_STACK_NAME} \
    ParameterKey=AppDescription,ParameterValue=${APP_STACK_NAME} \
    ParameterKey=IssuingTemplateName,ParameterValue=Default \
    ParameterKey=CertificateAuthority,ParameterValue=BUILTIN \
    ParameterKey=TLSPCAPIKey,ParameterValue=${TLSPCAPIKey}

# tlspc-certificate (create)
RandomKey=${RANDOM} && \
aws cloudformation create-stack \
  --stack-name ${CERT_STACK_NAME}-${RandomKey} \
  --template-url https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-certificate.yaml \
  --parameters \
    ParameterKey=Zone,ParameterValue=${APP_STACK_NAME}\\Default \
    ParameterKey=CommonName,ParameterValue=www${RandomKey}.example.com \
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