# TLSPC CloudFormation Automation - Venafi Ecosystem Workshop

## Introduction
* [00. Infrastructure As Code and AWS CloudFormation](00-iac-cloudformation/README.md)

## Technical Orientation
* [01. Requirements, Terminology and Disclaimers](01-requirements-terminology-and-disclaimers/README.md)
* [02. One-Time AWS Account Setup](02-one-time-aws-account-setup/README.md) (not required for Venafi/Jetstack Accounts)

## Workshop Exercises
* [03. TLSPC Policy Automation](03-tlspc-policy-automation/README.md)
* [04. TLSPC Certificate Automation](04-tlspc-certificate-automation/README.md)

## Teardown

**IMPORTANT** please do not delete any Stacks which you were not responsible for creating.

A polite reminder to Delete ALL of your Stacks after this workshop is complete.

- Navigate to https://us-east-1.console.aws.amazon.com/cloudformation/home
- **Carefully** enter your personalized identifier in the "Filter by stack name" field, and hit "Enter".
  If you completed the workshop, you should locate **THREE** Stacks.
- Select **each** of your Stacks one at a time and click the **"Delete"** button.

The order of deletion is not important and you needn't wait for any operation to complete before commencing the next.

## Appendices
* [101. Appendix - CloudFormation from AWS CLI](101-cloudformation-from-aws-cli/README.md)
