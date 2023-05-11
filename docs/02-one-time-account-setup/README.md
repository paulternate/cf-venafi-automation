# 02. One-Time Account Setup

## What's this all about?

Security teams need to strike a balance between granting enough privilege for staff to do the job, whilst staying secure.
Privilege escalation risks in AWS are contained by limiting what you're allowed to do, particularly with the Identity and Access Management (IAM) service.
Such limits can impact the standard workflow used when creating and deploying Lambda functions.
We can address this in each AWS account by pre-configuring an IAM Role for Lambda to use, but someone with elevated rights will need to apply the fix.

## What do I need to do?

**Answer: probably nothing.**

If you're using a Venafi/Jetstack AWS account today then the fix has likely been applied already so the following action is **not required** and you can move straight on with the [first exercise](../03-tlspc-create-application/README.md).

For anyone else, assuming you have the elevated rights required in your AWS account, you will need to apply this fix via CloudFormation.

If you're not sure, please consult your instructor.

## The Venafi CFN Setup Template

| Type | Description | S3 | Source |
| - | - | - | - |
| Template | Creates an IAM Role named VenafiLambdaBasicExecutionRole. This is for use by Lambda Functions, providing them with the ability to send logs to CloudWatch and interact with the S3 service for storage | https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/venafi-cfn-setup.yaml | [View](https://github.com/paulternate/cf-venafi-automation/blob/main/tlspc/templates/venafi-cfn-setup.yaml) |

## Steps to apply the fix

The following steps will enable Lambda Functions in the exercises to be successfully created.

- Navigate to https://us-east-1.console.aws.amazon.com/cloudformation/home
- Click on "Create stack", then click "With new resources (standard)"
- On the "Create stack" page, set "Amazon S3 URL" to `https://venafi-ecosystem.s3.amazonaws.com/tlspc/templates/venafi-cfn-setup.yaml`, then click "Next"
- On the "Specify stack details" page, set "Stack name" to something appropriate, like, `venafi-cfn-setup`, then click "Next"
- Scroll to the foot of the "Configure stack options" page, then click "Next"
- Scroll to the foot of the "Review" page, check ✅ the "Capabilities" checkbox and finally click "Submit"

After ~30 secs, the stack will reach a "Staus" of "CREATE_COMPLETE".
You will now be able to continue with the exercises in this workshop.

NOTE: You ran the Template in the "us-east-1" region.
Like most AWS services, CloudFormation is regionally scoped. However, the IAM resources it creates are global, so it's not particularly important where it runs ... in case you were wondering.

Next: [Main Menu](../README.md) | [03. CloudFormation Creates Application in TLSPC](../03-tlspc-create-application/README.md)
