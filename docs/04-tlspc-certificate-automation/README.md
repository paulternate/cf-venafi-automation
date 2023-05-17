# 04. TLSPC Certificate Automation

```
TLSPCAPIKey=<API_KEY_FROM_TLSPC>
PrivateKeyPassphrase=<PRIVATE_KEY_PASSPHRASE>

RandomKey=${RANDOM} && \
aws cloudformation create-stack \
  --stack-name amcginlay-cert-${RandomKey} \
  --template-url https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-certificate.yaml \
  --parameters \
    ParameterKey=Zone,ParameterValue=amcginlay-app\\Default \
    ParameterKey=CommonName,ParameterValue=www${RandomKey}.example.com \
    ParameterKey=TLSPCAPIKey,ParameterValue=${TLSPCAPIKey} \
    ParameterKey=PrivateKeyPassphrase,ParameterValue=${PrivateKeyPassphrase} \
    ParameterKey=TargetS3Bucket,ParameterValue= \
    ParameterKey=UpdateTrigger,ParameterValue=

aws cloudformation update-stack \
  --stack-name amcginlay-cert-${RandomKey} \
  --use-previous-template \
  --parameters \
    ParameterKey=Zone,UsePreviousValue=true \
    ParameterKey=CommonName,UsePreviousValue=true \
    ParameterKey=TLSPCAPIKey,UsePreviousValue=true \
    ParameterKey=PrivateKeyPassphrase,UsePreviousValue=true \
    ParameterKey=TargetS3Bucket,UsePreviousValue=true \
    ParameterKey=UpdateTrigger,ParameterValue=$(uuidgen)
```

Next: [Main Menu](../README.md) | [05. TLSPC Issuing Template Automation](../05-tlspc-issuing-template-automation/README.md)
