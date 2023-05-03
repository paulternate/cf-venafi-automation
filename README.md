# cf-venafi-automation - (WIP)

CloudFormation templates and accompanying files necessary for machine identity automation using the Venafi Control Plane.

## Tech Training - Venafi Ecosystem Session
The Venafi Ecosystem Session is accessible [here](docs/README.md)

## Parameters & Options

This is a flexible template that allows you to choose your desired level of automation, from creating everything in TLS Protect Cloud (Issuing Template, Application, and Certificate) to just requesting the certificate for your existing application.

**The following parameters are required for ALL options:**

<!-- Table for listing required parameters -->
| Parameter | Description | Default | Example | Required |
| :---: | --- | :---: | :---: | :---: |
| `TLSPCAPIKey` | TLS Protect Cloud API Key | *none* | `3ed81b56-c43d-426a-8d49-5855f8a91faf` | Always |
| `CommonName` | Common Name of the certificate to be requested | *none* | `test.example.com` | Always |

### Option 1: Create Everything

This option will create a new Application and Issuing Template in TLS Protect Cloud, and then request a certificate for the application.

>**NOTE:** As part of this process, a new Machine Type called "AWS CFN" will be created in TLS Protect Cloud. This is necessary to allow the certificate request to be made from the CloudFormation template.

The following parameters are required:

| Parameter | Description | Default | Example |
| :---: | --- | :---: | :---: |
| `TLSPCAPIKey` | TLS Protect Cloud API Key | *none* | `3ed81b56-c43d-426a-8d49-5855f8a91faf` |
| `CommonName` | Common Name of the certificate to be requested | *none* | `test.example.com` |
| `AppName` | Name of the application to be created in TLS Protect Cloud | `Test App` | `Test App` |
| `AppOwnerType` | Either `USER` or `TEAM` to designate the type of the AppOwner parameter | `USER` | `USER` |
| `AppOwner` | UUID of the User/Team to be designated as the owner of the application in TLS Protect Cloud - if not provided, the USER making the request will default to the owner | *none* | `c9b2bc00-bdce-11ed-bdff-8d873671b5c3` |
| `TemplateUrl` | URL of the issuing template policy (JSON) to be created in TLS Protect Cloud - [EXAMPLES](/venafi-policy-examples/) | `https://raw.githubusercontent.com/paulternate/cf-venafi-automation/main/venafi-policy-examples/open-issuing-template.json` | `https://raw.githubusercontent.com/paulternate/cf-venafi-automation/main/venafi-policy-examples/open-issuing-template.json` |
### Option 2: Existing Issuing Template

This will create a new Application in TLS Protect Cloud, assign the existing Issuing Template to it, and then request a certificate for the application.

>**NOTE:** As part of this process, a new Machine Type called "AWS CFN" will be created in TLS Protect Cloud. This is necessary to allow the certificate request to be made from the CloudFormation template.

The following parameters are required:

| Parameter | Description | Default | Example |
| :---: | --- | :---: | :---: |
| `TLSPCAPIKey` | TLS Protect Cloud API Key | *none* | `3ed81b56-c43d-426a-8d49-5855f8a91faf` |
| `CommonName` | Common Name of the certificate to be requested | *none* | `test.example.com` |
| `AppName` | Name of the application to be created in TLS Protect Cloud | `Test App` | `Test App` |
| `AppOwnerType` | Either `USER` or `TEAM` to designate the type of the AppOwner parameter | `USER` | `USER` |
| `AppOwner` | UUID of the User/Team to be designated as the owner of the application in TLS Protect Cloud - if not provided, the USER making the request will default to the owner | *none* | `c9b2bc00-bdce-11ed-bdff-8d873671b5c3` |
### Option 3: Existing Application
