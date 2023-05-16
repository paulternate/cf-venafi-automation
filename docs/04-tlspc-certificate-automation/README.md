# 04. TLSPC Certificate Automation


```
TLSPKAPIKey=<KEY_FROM_TLSPC>

aws cloudformation create-stack \
  --stack-name amcginlay-cert \
  --template-url https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-certificate.yaml \
  --parameters \
    ParameterKey=Zone,ParameterValue=amcginlay-app\\Default \
    ParameterKey=CommonName,ParameterValue=www${RANDOM}.example.com \
    ParameterKey=TLSPCAPIKey,ParameterValue=${TLSPKAPIKey} \
    ParameterKey=TargetS3Bucket,ParameterValue= \
    ParameterKey=RenewalTrigger,ParameterValue=

aws cloudformation update-stack \
  --stack-name amcginlay-cert \
  --use-previous-template \
  --parameters \
    ParameterKey=Zone,UsePreviousValue=true \
    ParameterKey=CommonName,UsePreviousValue=true \
    ParameterKey=TLSPCAPIKey,UsePreviousValue=true \
    ParameterKey=TargetS3Bucket,UsePreviousValue=true \
    ParameterKey=RenewalTrigger,ParameterValue=$(uuidgen)
```

Next: [Main Menu](../README.md) | [05. TLSPC Issuing Template Automation](../05-tlspc-issuing-template-automation/README.md)
