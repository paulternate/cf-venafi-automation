# 03. CloudFormation Creates Application in TLSPC

## What you will learn

In this section you will use CloudFormation (sometimes abbreviated to CFN) to deploy a Custom Resource representing a single Application in TLSPC.

## TLSPCApplication Templates and Functions

This exercise will make use of two objects stored in a publicly accessible S3 bucket.
They are as follows:

| Type | Description | S3 | Source |
| - | - | - | - |
| Template | Orchestrates the lifecycle of a TLSPCApplication Custom Resource which references the Function (deployed simultaneously) | https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-application.yaml | [View](../../tlspc/templates/tlspc-application.yaml)  |
| Function | Implements the Create/Update/Delete operations required by the TLSPCApplication Custom Resource | https://venafi-ecosystem.s3.amazonaws.com/tlspc/functions/tlspc-application.zip | [View](../../tlspc/functions/tlspc-application/app/app.py) |

## Creating the Stack

The following steps will register your Application in TLSPC.
This will be used later to create certificates.

**NOTE**: Unless otherwise stated, all settings should be left in their **DEFAULT** state.
Any warning banners which appear in the AWS Console during these steps are typically caused by policy restrictions in the target AWS account and can be safely **IGNORED**.

1. Navigate to https://us-east-1.console.aws.amazon.com/cloudformation/home
1. Click on "Create stack", then click "With new resources (standard)"
1. On the "Create stack" page, under "Specify template", set **"Amazon S3 URL"** to
   ```
   https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-application.yaml
   ```
   then click "Next"
1. On the "Specify stack details" page:
   - Set **"Stack name"** to something uniquely identifiable for **yourself, plus today's date**.
     Stack name can include letters (A-Z and a-z), numbers (0-9), and dashes (-).
     For Example, John Lennon could use
     ```
     johnlennon-23-06-01
     ```
   - Set **"AppName"** to the **same value** you just used for the "Stack name"
   - Set **"IssuingTemplateName"** to
     ```
     Default
     ```
     (see the NOTE below if this is missing from your account)
   - Set **"CertificateAuthority"** to
     ```
     BUILTIN
     ```
   - Set **"TLSPCAPIKey"** to whatever value is provided to you at https://ui.venafi.cloud/platform-settings/user-preferences?key=api-keys
   - Click "Next"
1. Scroll to the foot of the "Configure stack options" page, then click "Next"
1. Scroll to the foot of the "Review" page and finally click "Submit"

**NOTE**: A pristine TLSPC environment ships with the `Default` Issuing Template for the `Built-In CA`.
If your TLSPC environment has this Issuing Template renamed or is somehow missing, choose an alternate `Built-In CA` Issuing Template from the list shown at https://ui.venafi.cloud/certificate-issuance/issuing-templates.

After ~30 secs, the stack will reach a "Status" of "CREATE_COMPLETE".

At this point your Application will become visible at https://ui.venafi.cloud/certificate-issuance/applications

Next: [Main Menu](../README.md) | [04. CloudFormation Creates Issuing Template in TLSPC](../04-tlspc-create-issuing-template/README.md)

## Updating the Stack

TODO ... once the Description parameter is implemented.
