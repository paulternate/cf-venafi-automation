# 02. One-Time Account Setup

## NOTE 

This CloudFormation template requires the users to possess elevated rights which some users will **not** possess in the `venafi-se` and `venafi-ps` AWS accounts.
Attendees can assume that this step has been completed in advance and move straight on to the [next chapter](../03-tlspc-create-application/README.md)

## The template


and is a prerequisite in each target AWS account.
It is responsible for creating an IAM Role with the minimum rights



permits Lambda functions to create log entries in CloudWatch.
Since users may not themselves may not have the rights to create IAM Roles



It is included here for completeness but, in the case of the `venafi-se` and `venafi-ps` accounts you can assume this has been done already and move on to the [next chapter](../01/README.md)

Next: [Main Menu](/README.md) | [03. CloudFormation Creates Application in TLSPC](../03-tlspc-create-application/README.md)
