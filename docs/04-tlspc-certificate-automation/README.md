# 04. TLSPC Certificate Automation

## What you will learn

In this section you will use CloudFormation to deploy a Custom Resource representing a Certificate Request (CR) in TLSPC.
Each CR in TLSPC is tied to an Application, such as the one you created previously.
Upon successful issuance, each CR will be paired with exactly one Certificate in TLSPC.
All Key Material (i.e. Certificates and Private Keys) generated via TLSPC will be pulled into your AWS account and persisted to an S3 Bucket.

Timely Certificate renewal prevents outages.
In TLSPC, this is achieved by cloning and resubmitting the latest CR.
Over time, this sequence of CRs builds to create an audit trail for your Certificates.
In this exercise, you will employ the use of the Amazon EventBridge Scheduler to automate this process, ensuring that Certificate renewals always take place before the current latest Certificate expires. 

## TLSPCApplication Templates and Functions

This exercise will make use of three objects stored in a publicly accessible (read-only) S3 bucket.
They are as follows:

| Type | Description | S3 | Source |
| - | - | - | - |
| Template | Orchestrates the lifecycle of a TLSPCCertificate Custom Resource which references the Function. | https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-certificate.yaml | [View](../../tlspc/templates/tlspc-certificate.yaml)  |
| Function | Implements the Create/Update/Delete operations required by the TLSPCCertificate Custom Resource | https://venafi-ecosystem.s3.amazonaws.com/tlspc/functions/tlspc-certificate.zip | [View](../../tlspc/functions/tlspc-certificate/app/app.py) |
| Function | A dedicated instance of the `venafi-stack-updater` Function is pre-configured to invoke the Update method of this Stack. The frequency of invocation is determined by the associated EventBridge Schedule which is also deployed by the Template | https://venafi-ecosystem.s3.amazonaws.com/tlspc/functions/venafi-stack-updater.zip | [View](../../tlspc/functions/venafi-stack-updater/app/app.py) |

## A note on Defaults and warning messages

Unless otherwise stated, all console settings should be left in their **DEFAULT** state.

Any warning banners which appear in the AWS Console during these steps are typically caused by policy restrictions in the target AWS account and can be safely **IGNORED**.

## Creating your Certificate Stack

The following steps will model your Certificate Request requirements in a Cloudformation Stack, realize these inside TLSPC, persist the resultant key material and prevent future outages by ensuring timely renewals.

1. Navigate to https://us-east-1.console.aws.amazon.com/cloudformation/home
1. Click on "Create stack", then click "With new resources (standard)"
1. On the "Create stack" page, under "Specify template", set **"Amazon S3 URL"** to
   ```
   https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/tlspc-certificate.yaml
   ```
   then click "Next"
1. On the "Specify stack details" page:
   - Set **"Stack name"** to something uniquely identifiable for **yourself**, plus the letters "-cert".
     Stack name can include letters (A-Z and a-z), numbers (0-9), and dashes (-).
     For Example, George Harrison could use
     ```
     georgeharrison-cert
     ```
   - A **"Zone"** is a logical organizational units used for managing digital certificates.
     The typical form of a Zone is **AppName\IssuingTemplateAlias**.
     You already have a personalized Application from the previous exercise and this was mapped to the **"Default | BUILTIN"** Issuing Template using an Alias named **"Default"**.
     Carefully set this value to match your personal details.
     For example, George Harrison could use
     ```
     georgeharrison-app\Default
     ```
   - Set **"CommonName"** the subject/domain of the target template.
     In non-prod environments there is no requirement to own the domain so we advise you to set this value to something uniquely identifiable for **yourself**.
     For Example, George Harrison could use
     ```
     www.georgeharrison.com
     ```
   - **"ValidityHours"** is the number of hours your certificates should be considered valid.
     A Zero "0" here indicates you are willing to inherit this setting from the Zone's Issuing Template.
     Leave this setting unchanged, at
     ```
     0
     ```
   - **"RenewalHours"** is the interval in hours between certificate renewal requests.
     To protect from outages caused by certificate expiry, this value should be a number lower than the Validity period.
     The Validity period on this cert is likely to be the equivalent of 90 days, so set this value to 60 days, which converted to hours is
     ```
     1440
     ```
   - Set **"TLSPCAPIKey"** to whatever value is provided to you at https://ui.venafi.cloud/platform-settings/user-preferences?key=api-keys
   - Use **"PrivateKeyPassphrase"** to specify a password for encrypting the private key.
     Set this to something extremely difficult 😉 to guess, such as
     ```
     SuperSecret123!
     ```
   - **"TargetS3Bucket"** is the name of a versioned S3 Bucket where your TLSPC Certificates will be deposited.
     The Venafi One-Time Setup Template ensures that a default Bucket, named `venafi-tlspc-certificates-${AWS::AccountId}`, is available in your AWS account.
     For the purpose of this workshop, we advise that you leave this parameter **BLANK**.
   - **"UpdateTrigger"** is for internal use and only serves a non-functional purpose.
     We advise that you leave this parameter **BLANK**.
   - Click "Next"
1. Scroll to the foot of the "Configure stack options" page, then click "Next"
1. Scroll to the foot of the "Review" page and finally click "Submit"

After ~30 secs, the stack will reach a "Status" of "CREATE_COMPLETE".

## Reviewing your results (TLSPC)

Follow these instructions to view your newly created Certificate in TLSPC.
1. Navigate to https://ui.venafi.cloud/certificate-issuance/applications
1. Find and select the Application you created in the previous exercise
1. Click the **"View Certificates"** button
1. Locate the Certificate that matches the **"CommonName"** you provided earlier

## Reviewing your results (S3)

Follow these instructions to view your newly created Certificate in S3.
1. Navigate to https://us-east-1.console.aws.amazon.com/cloudformation/home?#/stacks
1. Locate your Stack and select it so the right-hand side panel displays the Stack Info tab
1. Locate the Outputs tab and select it
1. Find the Output Key named **"S#URL"** and click the URL shown in its Value column
1. You should see before you two files (`.cert` and `.key`) which match the CommonName of your certificate and contain its key material.

## Updating your Certificate Stack (Renewals)

CFN Stacks can be "Created" and "Deleted" only once, but "Updated" as many times as you like.
When you "Update" a regular CFN Stack it is typically because the template content or some parameters to the template need to be altered.
In the world of Machine Identities there's a domain-specific operation type, called a **"Renewal"**.
Renewals can be considered a form of "Soft-Update" in which the only material change to the inputs is the current date.
When machine identities are not renewed in a timely manner, outages occur.

The **"RenewalHours"** you specified above during Creation of the Certificate Stack determines when renewals happen but, as you don't have 60 days to wait around in this Workshop, you're going to simulate a renewal.

The following steps will cause a Certificate renewal in TLSPC.

1. Navigate to https://us-east-1.console.aws.amazon.com/cloudformation/home
1. Find or search for your Stack using the name you provided earlier
1. The Stack name is displayed as a blue hyperlink. Click this link now.
1. Toward the top-right of the console you will see four buttons.
   Locate the **"Update"** button and click it.
1. On the "Update Stack" page, click "Next" to reuse the existing template
1. Your intent for this Update operation is simply to renew the certificate so, technically, no parameter changes are required.
   However CloudFormation will reject the Update until at least parameter is changed.
   The parameter named **"UpdateTrigger"**, which serves no other functional purpose, exists to solve this problem.
   Set **"UpdateTrigger"** to:
   ```
   Venafi Ecosystem Rocks!
   ```
1. Click "Next"
1. Scroll to the foot of the "Configure stack options" page, then click "Next"
1. Scroll to the foot of the "Review" page and finally click "Submit"

After ~30 secs, the Stack will reach a "Status" of "UPDATE_COMPLETE".

## Reviewing your post-renewal results (TLSPC)

Using the instructions presented earlier in this exercise (see [Reviewing your results (TLSPC)](#reviewing-your-results-tlspc)) follow the instructions to view your updated Certificate in TLSPC.

This time you will observe that there are two Certificates for your Application, but one is now listed as **"(old)"**.
This indicates a successful renewal.

## Reviewing your post-renewal results (S3)

NOTE: To get the most benefit from these exercises, we recommend the use of Versioned S3 Buckets. If the Stacks you create in the exercise use the Bucket created by the One-Time Account Setup, this is taken care of for you.

Using the instructions presented earlier in this exercise (see [Reviewing your results (S3)](#reviewing-your-results-s3)) follow the instructions to view your updated Certificate in S3.

1. You should see before you two files (`.cert` and `.key`) which match the CommonName of your certificate and contain its key material.
1. **This time**, click through on the blue link for the `.cert` file.
1. You will observe three tabs: "Properties", "Permissions" and "Versions". Click **"Versions"**.

The behavior seen here mimics that which you observed with the **"(old)"** Certificates in TLSPC.
Like TLSPC, the **default** behavior in S3 is to always retrieve the current/latest version of any persisted object.
The archive of "old" versions are potentially useful for diagnostic or regulatory purposes and can be pruned later as necessary.

Next: [Main Menu](../README.md)
