# 03. TLSPC Policy Automation

## What you will learn

In this section you will use CloudFormation (sometimes abbreviated to CFN, or just CF) to deploy a Custom Resource representing a Policy.
In this context a Policy is represented by a pair of TLSPC resources, as follows.

- A **TLSPC Application** - A means to categorize policy-enforced collections of Certificate Requests and their Certificates.
- A **TLSPC Certificate Issuing Template** (CIT) - Used to configure security policies that are enforced whenever new Certificates are issued.
To enable a TLSPC CIT for use in policy enforcement it must first be associated with a TLSPC Application.

The choice to pair these resources under the term "Policy" was inspired by the implementation of VCert's [setpolicy](https://github.com/Venafi/vcert/blob/master/README-CLI-CLOUD.md#parameters-for-applying-certificate-policy) action, which condenses the functionality of the underlying resources down to their essential features.

## TLSPCPolicy Templates and Functions

This exercise will make use of two objects stored in a publicly accessible (read-only) S3 bucket.
They are as follows:

| Type | Description | S3 | Source |
| - | - | - | - |
| Template | Orchestrates the lifecycle of a TLSPCPolicy Custom Resource which references the Function | https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-policy.yaml | [View](../../tlspc/templates/tlspc-policy.yaml)  |
| Function | Implements the Create/Update/Delete operations required by the TLSPCPolicy Custom Resource | https://venafi-ecosystem.s3.amazonaws.com/tlspc/functions/tlspc-policy.zip | [View](../../tlspc/functions/tlspc-policy/app/app.py) |

## A note on Defaults and warning messages

Unless otherwise stated, all console settings should be left in their **DEFAULT** state.

Any warning banners which appear in the AWS Console during these steps are typically caused by policy restrictions in the target AWS account and can be safely **IGNORED**.

## Creating your Policy Stack

The following steps will model your Policy requirements in a Cloudformation Stack and realize these inside TLSPC.
The resulting Application and CIT in TLSPC will be used later to create certificates.

1. Navigate to https://us-east-1.console.aws.amazon.com/cloudformation/home
1. Click on "Create stack", then click "With new resources (standard)"
1. On the "Create stack" page, under "Specify template", set **"Amazon S3 URL"** to
   ```
   https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-policy.yaml
   ```
   then click "Next"
1. On the "Specify stack details" page:
   - Set **"Stack name"** to something uniquely identifiable for **yourself**, plus the letters "-policy".
     Stack name can include letters (A-Z and a-z), numbers (0-9), and dashes (-).
     For example, John Lennon could use
     ```
     johnlennon-policy
     ```
   - A **"Zone"** is a logical organizational unit used for managing digital certificates.
     The typical form of a Zone is **AppName\CertificateIssuingTemplateAlias**.
     As you can see this pairing aligns with the "Policy" definition described above.
     Set this value to match your personal details.
     For example, adopting the `-app` suffix to represent the Appliction and the `-cit` suffix to represent the CIT, John Lennon could use
     ```
     johnlennon-app\johnlennon-cit
     ```
   - The **"CertificateAuthority"** is expected to match one of the entries displayed at https://ui.venafi.cloud/certificate-issuance/certificate-authorities.
     Leave this setting unchanged, at
     ```
     Built-In CA
     ```
   - **"MaxValidDays"** is the maximum number of days for which any created/renewed certificate is considered valid.
     Leave this setting unchanged, at
     ```
     90
     ```
   - **"Domains"** is a list of domain names considered valid in the context of Certificates governed by this Policy.
     The template supports multiple domains names when provided as a comma-separated list.
     In non-prod environments there is no requirement to own these domains so we advise you to set this value to something uniquely identifiable for **yourself**.
     For Example, John Lennon could use
     ```
     johnlennon.com
     ```
   - Set **"TLSPCAPIKey"** to whatever value is provided to you at https://ui.venafi.cloud/platform-settings/user-preferences?key=api-keys
   - Click "Next"
1. Scroll to the foot of the "Configure stack options" page, then click "Next"
1. Scroll to the foot of the "Review" page and finally click "Submit"

After ~30 secs, the Stack will reach a "Status" of "CREATE_COMPLETE".

## Reviewing your results

At this point your newly created pair of TLSPC resources will become visible at the following URLs.

- **TLSPC Application** - https://ui.venafi.cloud/certificate-issuance/applications
- **TLSPC Certificate Issuing Template** - https://ui.venafi.cloud/certificate-issuance/issuing-templates

<!-- ## Updating your Application Stack

The following steps will update your Application in TLSPC.
In doing so, you will familiarize yourself with the process for updating Stacks in CloudFormation.

1. Navigate to https://us-east-1.console.aws.amazon.com/cloudformation/home
1. Find or search for your Stack using the name you provided earlier.
1. The Stack name is displayed as a blue hyperlink.
   Click this link now.
1. Take a moment to browse over tabs which are on display.
   Here are some observations regarding these tabs.
   - **Stack info** - This tab includes the system generated Stack ID. This is an example of an Amazon Resource Name (ARN) which is a system-generated identifier assigned to all AWS resources.
   These identifiers are universally unique within the AWS cloud.
   - **Events** - Details the steps CloudFormation has taken to (one hopes) successfully translate your parameterized Template into a Stack.
   The Events tab is usually your first port of call when investigating CloudFormation failures.
   - **Resources** - A list of the resources (Native AWS and Custom) which CloudFormation created for you. You will observe that your Stack has one Lambda Function and one TLSPCApplication.
   In the columm named Physical ID you will find a handy blue hyperlink to the Lambda function.
   The TLSPCApplication also has a collection of letters and numbers known as the Physical ID.
   **Ask yourself, what do you think this represents?**
   - **Outputs** - Outputs are selected informative results of successful runs. For example, if your stack creates a database entry CloudFormation could deposit a unique identifier here.
   - **Parameters** - A copy of the Parameters used when the Stack was Created or Updated.
   - **Template** - A copy of the Template used when the Stack was Created or Updated.
   - **Change sets** - This feature is beyond scope for today.
1. In the upper-right portion of the screen you will see 4 buttons.
   Locate the "Update" button and click it.
1. On the "Update stack" page, click "Next".
1. On the "Update stack" page, click "Next".
1. On the "Specify stack details" page:
   - Change **"AppDescription"** to
     ```
     I updated this TLSPC application!
     ```
   - Click "Next"
1. Scroll to the foot of the "Configure stack options" page, then click "Next"
1. Scroll to the foot of the "Review" page and finally click "Submit"

After ~30 secs, the stack will reach a "Status" of "UPDATE_COMPLETE".

At this point your newly updated TLSPC Application will become visible at https://ui.venafi.cloud/certificate-issuance/applications -->

Next: [Main Menu](../README.md)
