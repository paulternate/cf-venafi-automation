# 01. Requirements, Terminology and Caveats

## Requirements

To successfully complete this workshop you will need the following:

- Access to the "AWS Single Sign-on" (SSO) tile via https://venafi.okta.com/
- A minimum of "Basic" access to one of the following AWS accounts via SSO:
  - "venafi-se" (aka "Venafi SE")
  - "venafi-ps" (aka "AWS-PS")
  - Any personal account not belonging to Venafi/Jetstack (SSO not a requirement)
- Access to https://ui.venafi.cloud/ via either your own private domain or the company shared one
- The ability to distinguish between buses, stairs, bicycles and traffic lights! 😊

## Terminology

The following table covers a few terms which you'll see in this workshop and the minimum you need to know about them.

| Term  | Description |
| - | - |
| Template | The YAML or JSON file passed to CloudFormation which describes a collection of desired resources and their inter-dependencies. These resources are typically restricted to AWS, but not today! |
| Stack | When you provide parameters to a Template and "run" it, CloudFormation will transform your collection of desired resources into live resources with unique identifiers. A transformed collection of resources is referred to as a Stack. |
| EC2 | Amazon Elastic Compute Cloud (EC2) is the original AWS cloud computing service. It produces Virtual Machines which are billable regardless of their use. (You will not be using EC2) |
| S3 | Amazon Simple Storage Service (S3) is a scalable cloud storage service providing unlimited(!) storage and retrieval of data anywhere on the web. |
| Lambda | A compute service provided by AWS that allows you to run your code without having to provision or manage EC2 instances. Unlike EC2, Lambda only charges you for the time that your code is running. |
| Function | A piece of code uploaded to AWS Lambda which comes into existence and executes in response to specific events. Lambda Function instances are short-lived and stateless so they often use S3 for their persistence requirements. Lambda Functions are typically, but not exclusively, written in Python or NodeJS and can be invoked from Custom Resources. |

## Caveats

The Ecosystem team would like to clarify that this solution is by no means the finished article.
Coverage of the TLSPC API does not extend too far at this point and features you might expect to see will be missing.
The primary motivation for putting this workshop together was to establish a proof of concept, have you experience what's possible first-hand and get you thinking about what types of third-party integrations are valuable.

Maybe you think the Ecosystem team should focus their automation and IaC integration efforts elsewhere.
Or maybe you think we missed the point completely.
Either way, we'd love to know.
If customers are telling you they need something like this, but different in some way, let's work together to provide them with the tools they need to be "FastSecure".

Next: [Main Menu](../README.md) | [02. One-Time Account Setup](../02-one-time-account-setup/README.md)