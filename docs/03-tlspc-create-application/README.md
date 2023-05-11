# 03. CloudFormation Creates Application in TLSPC

## What you will learn

In this section you will use CloudFormation (which you may see abbreviated to CFN) to deploy a Custom Resource representing a single Application in TLSPC.

## TLSPCApplication Templates and Functions

This exercise will make use of two objects stored in a publicly accessible S3 bucket.
They are as follows:

| Type | Description | S3 | Source |
| - | - | - | - |
| Template | Orchestrates the lifecycle of a TLSPCApplication Custom Resource which references the Function (deployed simultaneously) | https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-application.yaml | [View](https://github.com/paulternate/cf-venafi-automation/blob/main/tlspc/templates/tlspc-application.yaml)  |
| Function | Implements the Create/Update/Delete operations required by the TLSPCApplication Custom Resource | https://venafi-ecosystem.s3.amazonaws.com/tlspc/functions/tlspc-application.zip | [View](https://github.com/paulternate/cf-venafi-automation/blob/main/tlspc/functions/tlspc-application/app/app.py) |

## Let's Go!



Next: [Main Menu](../README.md) | [04. CloudFormation Creates Issuing Template in TLSPC](../04-tlspc-create-issuing-template/README.md)

