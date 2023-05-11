# 03. CloudFormation Creates Application in TLSPC

## What is Infrastructure As Code?

Infrastructure as Code (IaC) is an approach to automating the management and provisioning of infrastructure resources using machine-readable definition files rather than manually configuring infrastructure components.
It involves writing code in a high-level language, such as YAML, to define the desired infrastructure.
Infrastructure declared this way can then be version-controlled, tested, and deployed in a reliable and consistent way.
By defining IaC, developers and operations teams can collaborate more effectively and ensure that infrastructure is consistent across all environments.

## What is AWS CloudFormation?

AWS CloudFormation is a service provided by Amazon Web Services (AWS) that allows users to define and deploy parameterized IaC templates into your AWS account.
Each template is capable of managing large collections of interdependent AWS resources, including EC2 instances, S3 buckets, SQS queues, RDS databases and so on.

Terraform by Hashicorp is a platform-independent alternative to AWS CloudFormation.

## What are Custom Resources?

Custom Resources are a feature of AWS CloudFormation that allow users to extend CloudFormation functionality by adding custom code to their templates.
This feature enables users to define new resource types, backed by serverless AWS Lambda functions, that are not natively supported by AWS CloudFormation.
Developers can define the code that will be executed when the Custom Resource is created, updated or deleted.

## Why is this important?

The Venafi Ecosystem team is tasked with making the consumption of Venafi services as frictionless as possible.
Imagine a Cloud Native company who is both a customer of AWS and a user of TLS Protect Cloud (TLSPC).
If they need to mint certificates via TLSPC before activating their AWS compute resources then you can conceptualize TLSPC as a deep-rooted dependency of their infrastructure.
The use of Custom Resources to model resources in TLSPC via its API allows us to treat TLSPC as an extension of AWS, ensuring that policy-enforced certificates are available at the point of need.

Next: [Main Menu](../README.md) | [04. CloudFormation Creates Issuing Template in TLSPC](../04-tlspc-create-issuing-template/README.md)

