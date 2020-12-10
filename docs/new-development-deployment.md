# Deploying a development version of the Aggregator API

* [Example output and AWS credentials](#example-output-and-aws-credentials)
* [Deploying into AWS Lambda](#deploying-into-aws-lambda)
   * [Installing local pre-requisites](#installing-local-pre-requisites)
   * [Setting up the configuration file](#setting-up-the-configuration-file)
   * [Validating your deployment template](#validating-your-deployment-template)
   * [Building the deployment artifact](#building-the-deployment-artifact)
   * [Deploying the built artifacts](#deploying-the-built-artifacts)
   * [Testing the deployment](#testing-the-deployment)
   * [Debugging problems](#debugging-problems)
      * [Viewing app logs](#viewing-app-logs)
      * [Enabling Django's DEBUG mode](#enabling-djangos-debug-mode)
      * [Lambda environment variables](#lambda-environment-variables)
* [Deploying TLS, CDN and DNS on top of an existing Lambda deployment](#deploying-tls-cdn-and-dns-on-top-of-an-existing-lambda-deployment)
   * [Choose a "public"-facing FQDN](#choose-a-public-facing-fqdn)
   * [Manual steps](#manual-steps)
      * [Create a domain](#create-a-domain)
      * [Delegate DNS authority to your new domain](#delegate-dns-authority-to-your-new-domain)
      * [Find the ACM ARN of a certificate that's valid for your domain](#find-the-acm-arn-of-a-certificate-thats-valid-for-your-domain)
   * [Preparing for deployment](#preparing-for-deployment)
   * [Deploying DNS+TLS+CDN](#deploying-dnstlscdn)
   * [Testing the deployment](#testing-the-deployment-1)
* [Tearing down deployments](#tearing-down-deployments)

This document describes 2 deployment scenarios, the second of which builds on the first:

1) [App](#deploying-into-aws-lambda): the API deployed as an app in AWS Lambda, accessed directly via AWS API Gateway
2) [Public Access](#deploying-tls-cdn-and-dns-on-top-of-an-existing-lambda-deployment): The Lambda app deployed in (1), accessed via a custom domain name, with a valid TLS certificate, fronted by a caching CDN.

In order to [deploy into Lambda](#deploying-into-aws-lambda) and then [deploy TLS, CDN and DNS on top](#deploying-tls-cdn-and-dns-on-top-of-an-existing-lambda-deployment), you'll need to be deploying into an AWS account that's been set up as per the [AWS account setup document](/docs/new-aws-account-setup.md).

[Tearing down deployments](#tearing-down-deployments) is described at the end of this document.

## Example output and AWS credentials

In this document, the `jcm1` environment will be deployed to show example output, using `pipenv run` as a prefix to activate a virtualenv containing the appropriate dev tools. You can activate or use such a virtualenv however suits you best.

Make your AWS credentials available to the shell. Environment variables work well, as does having a setup baked into your user-level configuration files (https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html).

## Deploying into AWS Lambda

### Installing local pre-requisites

After cloning the repo, use pipenv to install the dev packages. Avoid Pipenv version 11.9, unfortunately baked into recent Ubuntu releases, as it's broken in various Pipfile-processing ways (https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=945139).

### Setting up the configuration file

Use the script `samconfig.toml.d/new-dev-env.py` to clone the `[EXAMPLE]` and `[EXAMPLE-public-access]` sections and subsections, substituting `EXAMPLE` for a new deployment name of your choice. If you choose a new environment name composed of the characters "a" through "z" and "0" through "9" then everything has the best chance of working. If you also use characters in the set `[-_A-Z]` then things _might_ work. Using periods will definitely break several DNS-based limitations: don't do that.

```
$ NEW_ENV_NAME=myenv pipenv run python samconfig.toml.d/new-dev-env.py >>samconfig.toml
```

To achieve the same result without using the script, edit `samconfig.toml.d/development`. Clone the `[EXAMPLE]` and `[EXAMPLE-public-access]` top-level sections, including all their subsections. For this deployment, only the `[EXAMPLE.deploy.parameters]` section *needs* to have each occurrence of the `EXAMPLE` text changed to an environment name of your choice, but you should change every instance right now. Just do a simple find'n'replace.

You can commit your changes to `samconfig.toml.d/development`, so long as you've not included any sensitive parameters. At the time of writing, the AppSecretKey, CertificateArn and PublicFqdn settings aren't considered sensitive in development deployments.

The `sam` CLI will be your main deployment tool. *Every* time you invoke it, you *must* pass it the name of the environment you just created in `samconfig.toml.d/development` as the `--config-env <new-env-name>` parameter. The config file is a) symlinked into the default `samconfig.toml` location in the repo for convenience and b) deliberately doesn't include a `default` environment, in order to avoid namespace collisions between DC devs in the event of anyone forgetting to provide the `--config-env <new-env-name>` parameter to `sam`.

If you forget to provide the `--config-env` parameter, or provide an non-existent env name, then you'll see this unhelpful error:

```
$ pipenv run sam deploy # missing: --config-env <anything>
Usage: sam deploy [OPTIONS]
Try 'sam deploy --help' for help.

Error: Missing option '--stack-name', 'sam deploy --guided' can be used to provide and save needed parameters for future deploys.

$ pipenv run sam deploy --config-env INVALID
Usage: sam deploy [OPTIONS]
Try 'sam deploy --help' for help.

Error: Missing option '--stack-name', 'sam deploy --guided' can be used to provide and save needed parameters for future deploys.
```

If your intention is to deploy the app and then *immediately* wrap it in TLS/CDN/DNS (as per section 2 of this document), change your new environment's `AppIsBehindCloudFront` setting in `samconfig.toml.d/development` to be `True`. Changing this setting requires a redeployment of the app (but not TLS/CDN/DNS), but since a redeployment doesn't take very long it's a step you can easily perform later.

### Validating your deployment template

Validating the template contacts the AWS API, so can't be done offline. This one `sam` command doesn't seem to obey any sections in the `samconfig.toml.d/development` file, but it *does* need to know which AWS region to contact. Rather than inject the implict knowledge into future `sam` commands by exporting the `AWS_DEFAULT_REGION` environment variable for this entire session, or more permanently, here we can just prepend *this one* command with the variable. Don't use this method for any other `sam` commands.

```
$ AWS_DEFAULT_REGION=eu-west-2 pipenv run sam validate
/home/ubuntu/code/aggregator-api/template.yaml is a valid SAM Template
```

### Building the deployment artifact

Use the Makefile's default target to:

- delete and recreate the static asset directory at `aggregator/static_files`
- generate `lambda-layers/DependenciesLayer/requirements.txt`

The results of these steps are gitignored, and have to be re-done when you change either Pipfile/.lock or anything that alters how the static assets look.

```
$ pipenv run make
rm -rf aggregator/static_files/ lambda-layers/DependenciesLayer/requirements.txt
python manage.py collectstatic --noinput --clear
Copying '/home/ubuntu/code/aggregator-api/aggregator/assets/images/dc-badge/black/badge.png'
[ ... 133 "Copying" lines elided ... ]
Post-processed 'css/styles.css' as 'css/styles.css'
[ ... 111 "Post-processed" lines elided ... ]
134 static files copied to '/home/ubuntu/code/aggregator-api/aggregator/static_files', 139 post-processed.
pipenv lock -r | sed "s/^-e //" >lambda-layers/DependenciesLayer/requirements.txt
```

Build the Lambda deployment package (NB this will *destroy* the current contents of the `.aws-sam/build/` directory, which probably only contains your previous build):

```
$ pipenv run sam build --config-env jcm1 --use-container
Starting Build inside a container
Building codeuri: . runtime: python3.6 metadata: {} functions: ['AggregatorApiFunction']
Fetching amazon/aws-sam-cli-build-image-python3.6 Docker container image......
Mounting /home/ubuntu/code/aggregator-api as /tmp/samcli/source:ro,delegated inside runtime container
Running PythonPipBuilder:ResolveDependencies
Running PythonPipBuilder:CopySource
Building layer 'DependenciesLayer'
For container layer build, first compatible runtime is chosen as build target for container.

Fetching amazon/aws-sam-cli-build-image-python3.6 Docker container image......
Mounting /home/ubuntu/code/aggregator-api/lambda-layers/DependenciesLayer as /tmp/samcli/source:ro,delegated inside runtime container

Build Succeeded

Built Artifacts  : .aws-sam/build
Built Template   : .aws-sam/build/template.yaml

Commands you can use next
=========================
[*] Invoke Function: sam local invoke
[*] Deploy: sam deploy --guided

Running CustomMakeBuilder:CopySource
Running CustomMakeBuilder:MakeBuild
Current Artifacts Directory : /tmp/samcli/artifacts
```

Note the use of `--use-container`, here. This is recommended for build/dev environment isolation, but isn't essential. It requires docker to be installed, and for your user to be able to start containers without the use of `sudo`. If that's not possible, you can build without `--use-container`.

The build artifacts have been placed in the `.aws-sam/build/` directory. Note the presence of the file `.aws-sam/build/template.yaml`: this is the CloudFormation template that will be deployed in the next step; if you modify the source `template.yaml` file in the root of the repo and want to deploy those changes, you'll need to re-run the build. Whilst it's *possible* to make changes directly to `.aws-sam/build/template`, hence allowing a redeployment without a rebuild (sometimes useful when rapidly iterating on infra- or AWS-related changes), do keep in mind that **all your changes made this way will be lost the next time you build**!

### Deploying the built artifacts

Use the `sam` CLI to deploy the app. You'll need to have at least the AWS IAM permissions mentioned in the [AWS account setup document](/docs/new-aws-account-setup.md#policies). Once you have seen the 3 uploads complete (currently: 3MB app; 28MB dependencies layer; 1KB template), the CloudFormation Stack creation should take no more than a minute - or something's not right.

```
$ pipenv run sam deploy --config-env jcm1
	Deploying with following values
	===============================
	Stack name                   : AggregatorApiApp-jcm1
	Region                       : eu-west-2
	Confirm changeset            : False
	Deployment s3 bucket         : aggregator-api-deployment-artifacts-development-075b482c18
	Capabilities                 : ["CAPABILITY_IAM"]
	Parameter overrides          : {'AppDjangoSettingsModule': 'aggregator.settings.lambda_no_debug_merged_assets', 'AppSecretKey': 'badf00d', 'AppIsBehindCloudFront': 'False'}
	Signing Profiles           : {}

Initiating deployment
=====================
AggregatorApiFunction may not have authorization defined.
AggregatorApiFunction may not have authorization defined.
Waiting for changeset to be created..
CloudFormation stack changeset
---------------------------------------------------------------------------------------------------------------------------------------------
Operation                           LogicalResourceId                   ResourceType                        Replacement
---------------------------------------------------------------------------------------------------------------------------------------------
+ Add                               AggregatorApiFunctionHTTPRequestR   AWS::Lambda::Permission             N/A
                                    ootsPermissionProd
+ Add                               AggregatorApiFunctionHTTPRequests   AWS::Lambda::Permission             N/A
                                    PermissionProd
+ Add                               AggregatorApiFunction               AWS::Lambda::Function               N/A
+ Add                               DependenciesLayera71d191a6f         AWS::Lambda::LayerVersion           N/A
+ Add                               ServerlessRestApiDeploymentf33e89   AWS::ApiGateway::Deployment         N/A
                                    2db2
+ Add                               ServerlessRestApiProdStage          AWS::ApiGateway::Stage              N/A
+ Add                               ServerlessRestApi                   AWS::ApiGateway::RestApi            N/A
---------------------------------------------------------------------------------------------------------------------------------------------
Changeset created successfully. arn:aws:cloudformation:eu-west-2:489559689862:changeSet/samcli-deploy1607352403/13b8e28d-bc8c-43f6-a3da-20a6e42372d0
2020-12-07 14:46:49 - Waiting for stack create/update to complete
CloudFormation events from changeset
---------------------------------------------------------------------------------------------------------------------------------------------
ResourceStatus                      ResourceType                        LogicalResourceId                   ResourceStatusReason
---------------------------------------------------------------------------------------------------------------------------------------------
CREATE_IN_PROGRESS                  AWS::Lambda::LayerVersion           DependenciesLayera71d191a6f         -
CREATE_COMPLETE                     AWS::Lambda::LayerVersion           DependenciesLayera71d191a6f         -
CREATE_IN_PROGRESS                  AWS::Lambda::LayerVersion           DependenciesLayera71d191a6f         Resource creation Initiated
CREATE_IN_PROGRESS                  AWS::Lambda::Function               AggregatorApiFunction               -
CREATE_IN_PROGRESS                  AWS::Lambda::Function               AggregatorApiFunction               Resource creation Initiated
CREATE_COMPLETE                     AWS::Lambda::Function               AggregatorApiFunction               -
CREATE_IN_PROGRESS                  AWS::ApiGateway::RestApi            ServerlessRestApi                   Resource creation Initiated
CREATE_IN_PROGRESS                  AWS::ApiGateway::RestApi            ServerlessRestApi                   -
CREATE_COMPLETE                     AWS::ApiGateway::RestApi            ServerlessRestApi                   -
CREATE_IN_PROGRESS                  AWS::Lambda::Permission             AggregatorApiFunctionHTTPRequests   Resource creation Initiated
                                                                        PermissionProd
CREATE_IN_PROGRESS                  AWS::Lambda::Permission             AggregatorApiFunctionHTTPRequests   -
                                                                        PermissionProd
CREATE_IN_PROGRESS                  AWS::Lambda::Permission             AggregatorApiFunctionHTTPRequestR   -
                                                                        ootsPermissionProd
CREATE_IN_PROGRESS                  AWS::ApiGateway::Deployment         ServerlessRestApiDeploymentf33e89   -
                                                                        2db2
CREATE_COMPLETE                     AWS::ApiGateway::Deployment         ServerlessRestApiDeploymentf33e89   -
                                                                        2db2
CREATE_IN_PROGRESS                  AWS::Lambda::Permission             AggregatorApiFunctionHTTPRequestR   Resource creation Initiated
                                                                        ootsPermissionProd
CREATE_IN_PROGRESS                  AWS::ApiGateway::Deployment         ServerlessRestApiDeploymentf33e89   Resource creation Initiated
                                                                        2db2
CREATE_IN_PROGRESS                  AWS::ApiGateway::Stage              ServerlessRestApiProdStage          -
CREATE_IN_PROGRESS                  AWS::ApiGateway::Stage              ServerlessRestApiProdStage          Resource creation Initiated
CREATE_COMPLETE                     AWS::ApiGateway::Stage              ServerlessRestApiProdStage          -
CREATE_COMPLETE                     AWS::Lambda::Permission             AggregatorApiFunctionHTTPRequests   -
                                                                        PermissionProd
CREATE_COMPLETE                     AWS::Lambda::Permission             AggregatorApiFunctionHTTPRequestR   -
                                                                        ootsPermissionProd
CREATE_COMPLETE                     AWS::CloudFormation::Stack          AggregatorApiApp-jcm1               -
---------------------------------------------------------------------------------------------------------------------------------------------
CloudFormation outputs from deployed stack
------------------------------------------------------------------------------------------------------------------------------------------------
Outputs
------------------------------------------------------------------------------------------------------------------------------------------------
Key                 AggregatorApiFqdn
Description         API Gateway endpoint FQDN for Aggregator API function
Value               uod8dodf03.execute-api.eu-west-2.amazonaws.com
------------------------------------------------------------------------------------------------------------------------------------------------
Successfully created/updated stack - AggregatorApiApp-jcm1 in eu-west-2
```

Notice that the "AggregatorApiFqdn" CloudFormation Output is shown here: this is the Fully Qualified Domain Name ("FQDN") on which the app is available, but isn't the full *URL* that needs to be requested in order to reach the app. The app is only available over HTTPS (although an HTTP request will redirect to HTTPS), and only with the API Gatway "Stage" appended. In the case of deployments orchestrated by the `sam` CLI, which first modifies the template you provide and then asks CloudFormation to apply the [AWS Serverless Transform](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/transform-aws-serverless.html), this stage is always "Prod".

Thus, the URL that reaches the app is `https://{AggregatorApiFqdn}/Prod`; in the example `jcm1` deployment's case this is `https://uod8dodf03.execute-api.eu-west-2.amazonaws.com/Prod`.

Whilst this URL isn't explicitly secret, avoid publishing it publically. All requests to this URL *will* be served by a chargeable Lambda function invocation - the CloudFront distribution that you might notice is inline (by examining HTTP response headers) is *not* configured to do any caching; it's only an internal AWS implementation detail.

### Testing the deployment

Use the pytests in `.circleci/tests/system/test_app_via_api_gateway.py` to check the deployment is working as intended.

Teach the tests about your config env by setting the `SAM_LAMBDA_CONFIG_ENV` environment variable appropriately:

```
$ SAM_LAMBDA_CONFIG_ENV=jcm1 pipenv run pytest -vrP --disable-warnings .circleci/tests/system/test_app_via_api_gateway.py
================================================== test session starts ====================================================
platform linux -- Python 3.8.5, pytest-6.1.2, py-1.9.0, pluggy-0.13.1 -- /home/ubuntu/.local/share/virtualenvs/8/bin/python
cachedir: .pytest_cache
django: settings: aggregator.settings.testing (from ini)
rootdir: /home/ubuntu/code/aggregator-api, configfile: pytest.ini
plugins: flakes-4.0.3, django-3.10.0, cov-2.10.1
collected 1 item

.circleci/tests/system/test_app_via_api_gateway.py::test_app_front_page_http_200 PASSED                                [100%]

=========================================================== PASSES ========================================================
================================================ 1 passed, 7 warnings in 5.43s ============================================
```

### Debugging problems

#### Viewing app logs

App logs are shipped by Lambda into CloudWatch Logs, with a default retention of 2 months. To view them, make sure your environment in `samconfig.toml` has appropriately copied and modified `[<env-name>.logs]`/`[<env-name>.logs.parameters]` sections. Then, use the `sam` CLI to tail (with `--tail`) or view (without `--tail`) the most recent logs:

```
$ pipenv run sam logs --config-env jcm1
2020/12/07/[$LATEST]70e6068f1e704bdfad78fdd8eab994d3 2020-12-07T21:39:29.460000 START RequestId: 4b3d24d7-af3a-44f6-9f3b-89d1200d0030 Version: $LATEST
2020/12/07/[$LATEST]70e6068f1e704bdfad78fdd8eab994d3 2020-12-07T21:39:34.455000 END RequestId: 4b3d24d7-af3a-44f6-9f3b-89d1200d0030
2020/12/07/[$LATEST]70e6068f1e704bdfad78fdd8eab994d3 2020-12-07T21:39:34.455000 REPORT RequestId: 4b3d24d7-af3a-44f6-9f3b-89d1200d0030  Duration: 4994.93 ms Billed Duration: 4995 ms Memory Size: 192 MB     Max Memory Used: 99 MB  Init Duration: 1080.62 ms
2020/12/07/[$LATEST]70e6068f1e704bdfad78fdd8eab994d3 2020-12-07T21:40:03.709000 START RequestId: 0e3eb1de-4a6a-41c8-bc9b-7d33b5a380ec Version: $LATEST
2020/12/07/[$LATEST]70e6068f1e704bdfad78fdd8eab994d3 2020-12-07T21:40:03.716000 END RequestId: 0e3eb1de-4a6a-41c8-bc9b-7d33b5a380ec
2020/12/07/[$LATEST]70e6068f1e704bdfad78fdd8eab994d3 2020-12-07T21:40:03.716000 REPORT RequestId: 0e3eb1de-4a6a-41c8-bc9b-7d33b5a380ec  Duration: 3.55 ms    Billed Duration: 4 ms    Memory Size: 192 MB     Max Memory Used: 99 MB
```

Note that this example shows the default/HTTP-200/happy-path access logs; also note how unhelpful they are. The logs *do* receive stdout and stderr if any part of the app emits text there, including stack traces and exceptions. The logs appear to be more useful for debugging problems than for tracking usage or performance over time.

#### Enabling Django's DEBUG mode

Django's debug mode is trivially engaged by:

- modifying an enviroment's `AppDjangoSettingsModule` parameter override setting in the appropriate `samconfig.toml` file
- redeploying with `sam deploy`

No rebuild is needed if moving between any of the 4 convenience settings shims present in `aggregator/settings/`, as they all (currently) produce the same superset of static assets on disk. The shims are:

- `lambda_no_debug_merged_assets`: debug disabled; the default setting, present in all CI-deployed environments
- `lambda_no_debug_unmerged_assets`: debug disabled
- `lambda_debug_merged_assets`: debug enabled
- `lambda_debug_unmerged_assets`: debug enabled

Both "merged assets" shims set `PIPELINE["PIPELINE_ENABLED"] = True`; "unmerged assets" configures the same setting as `False`.

#### Lambda environment variables

[Skip this section if you're deploying the existing codebase, and don't need to set a new environment variable]

To set a new variable in your function's environment in Lambda, first decide if this parameter can be fixed across every environment (temporary developer deployments, and the 3 CI-managed deployments: developement, staging and production). If it can be, simply add a new key to the `Variables` section in `template.yaml`. This section is at the path `Resources >> AggregatorApiFunction >> Properties >> Environment >> Variables`. Add the key/value pair that you want the app to see, and rebuild+redeploy.

If using a fixed value isn't possible, then you'll need to use a CloudFormation "Parameter", and the `samconfig.toml` "parameter override" section to communicate the values to the CloudFormation template.

Use the existing Parameter `AppDjangoSettingsModule` as a guide.

Notice that:

- It's named with an "App" prefix to give humans a visual indicator that it's a parameter that directly affects the app, and not some other component that's deployed alongside Lambda; the *Parameter* **name** is a reference for the developer/operator, and should be chosen to make their lives easier. It has nothing *directly* to do with the environment variable name that's passed to the app!
- It's set in the `Parameters` top-level section of `template.yaml`
- It's referenced in the `Variables` section (at `Resources >> AggregatorApiFunction >> Properties >> Environment >> Variables`)
- It's configured externally in `samconfig.toml` for developer deployments
- It's configured externally in `.circleci/config.yml` in the `sam_deploy` job **for CI-managed deployments**

CloudFormation Parameters can have default values: see `AppLogRetentionDays` as an example of how this is specified.

If you *don't* set a default, you must make sure that each CI deployment has a value injected (in the `sam_deploy` job) **or the deployment following your commit to `template.yaml` will fail**.

Some things to note:

1. Parameter defaults are sticky. The first time a default is used by a CloudFormation Stack, that default value becomes the Parameter value for the Stack. Changing *the default* won't affect currently-deployed Stacks: only explicitly setting a Parameter value will change the value in currently-deployed Stacks.
1. If you choose not to set a default (which is a perfectly valid choice) then you're forcing every deployment to explicitly specify a value before they next deploy. Deployments will fail early if they lack such a value.

## Deploying TLS, CDN and DNS on top of an existing Lambda deployment

Once the Lambda deployment is working, you can optionally deploy a custom domain and CDN/caching in front of it. This should be considered mandatory for any deployment being consumed by public/non-DC users and is implemented for all CI-managed deployments exactly as shown here.

### Choose a "public"-facing FQDN

To begin, choose the Fully Qualified Domain Name ("FQDN") via which you want users to access this deployment.

In the development environment, there is already infra set up to enable a direct subdomain of `environments.womblelabs.co.uk` and it makes sense for your FQDN to be a subdomain of that.

Unless you have a reason to do otherwise, choose an FQDN matching `<ENV>.environments.womblelabs.co.uk`, where `<ENV>` is your deployment's name. When you constructed that name (in [section 1](#setting-up-the-configuration-file) of this document) it was suggested to choose a name that only uses the characters `[a-z0-9]`. If you've also included a hyphen in your environment's name, things will probably still work, but consider removing it. If you've included any periods, *definitely* remove them as they won't work with the DNS guidance below.

In the example output below, the FQDN `jcm1.environments.womblelabs.co.uk` is shown.

### Manual steps

There are a couple of manual infra-related steps to perform, which don't make sense to include in the deployment automation. These only need to be performed once per development environment, and the ongoing cost of leaving this per-environment infra in place is minimal.

#### Create a domain

For technical reasons around dev/prod environment parity when the app is be presented over the FQDN `a.b.c.d` the domain `a.b.c.d` needs to be created and delegated correctly from `b.c.d` (or a parent domain). If you feel this sounds subtly wrong, you're correct; it is, however, the easiest way to keep all environments' setups the same, whilst allowing DC to manage its top-level domains separately from any one product. It's a trade off; the cost of which is $6/year/environment (AWS prices are currently $0.50/month/domain) and the manual steps you have to perform, right now. Don't worry: they're painless and quick!

Sign in to AWS as a user who can create domains in Route53. Once logged in go to [the Route53 UI](https://console.aws.amazon.com/route53/home#hosted-zones:). Revert to the "old" user interface if the "new" one loads; the "new" one is a horrendous blight and should be avoided as long as the option is there to revert.

Go to the list of Hosted Zones, and note 2 of the zones that are present as subdomains of the DC staging domain: `environments.womblelabs.co.uk` and `developers.environments.womblelabs.co.uk`.

The `developers.environments.womblelabs.co.uk` zone is the one created for the CI-managed "development" deployment. Don't touch this one as part of this process.

Create your new zone, named the same as the FQDN you chose above.

#### Delegate DNS authority to your new domain

After creating your new domain, go to its Record Set list and find the automatically-created `NS` record. Its value should be 4 FQDNs on 4 seperate lines; copy this value, including the trailing period on each line.

Find a parent zone of this zone. In the case of a developer domain, this will usually be `environments.womblelabs.co.uk`.

In the parent zone's Record Set's list, create a Record Set:

* Name: put the `<ENV>` name in the box, so that the UI-constructed name reads `<ENV>.environments.womblelabs.co.uk`
* Type: `NS`
* TTL: click the "1h" button (this isn't hugely important; don't worry if it isn't correct)
* Value: paste the 4-line `NS` records you copied from the newly-created zone, ensuring each FQDN has a trailing period

#### Find the ACM ARN of a certificate that's valid for your domain

NB If the FQDN you chose is a direct subdomain of `environments.womblelabs.co.uk`, then the certificate ARN you copied when cloning the `[EXAMPLE-public-access.deploy-parameters]` section in `samconfig.toml` is valid, and you can skip this section. If not ...

In the [AWS Certificate Manager service UI](https://console.aws.amazon.com/acm/home?region=us-east-1#/), make sure you're looking at the "US East (N. Virginia)"/us-east-1 region. CloudFront, which will terminate TLS/HTTPS connections for your deployment's domain, **can only deploy ACM certificates created in the us-east-1 region**. (This annoyance is why it hasn't yet made sense to automate this and the 2 DNS-related manual steps: CloudFormation Stacks can only create Resources in a single region, unless the more complex Stack Set product is used).

The account admin should have created a certificate that covers your domain. Keeping these few TLS nuances in mind, find the certificate that you'll use:

* Names in either the "Domain name" or "Additional names" columns are equivalent and sufficient. It doesn't matter in which column the matching entry exists, except that the "Name" column is *not* sufficient and should be ignored.
* TLS wildcards, expressed as asterisks in the relevant "name" column, can't cross period-boundaries. A certificate for `*.foo.com` can only protect `www.foo.com` and *not* `www.env.foo.com`.
* TLS wildcards can't be ignored. A certificate for `*.foo.com` can't protect `foo.com`.
* If there are multiple certificates which could protect your deployment, then in the development environment it doesn't really matter which one you use. Another user can't delete a certificate while your deployment is using it so, apart from administrative tidyness, choosing any valid certificate is ok.

If there's no valid certificate for your FQDN, but you believe there should be **double-check that you're looking at the us-east-1 region**. Certificates only exist in a single region: the one in which they were created.

If there's *still* no valid certificate for your FQDN, you can create one. [Follow this guidance](https://docs.aws.amazon.com/acm/latest/userguide/gs-acm-request-public.html#request-public-console), and choose "DNS validation" when asked. So long as you're in the same AWS account that owns the domain you created, above, you can use the ACM UI -- after creation and during the certificate's "Validation" step -- to "Create record in Route 53".

Create a certificate that has a "Domain name" equal to your FQDN, validate it, and go back to the certificate table.

Expand the details of your chosen certificate -- either one of those already present, or one you just created -- by clicking anywhere on the certificate's entry in the table.

Find and copy the certificate's ARN (globally unique, internal AWS identifier), which will look something like `arn:aws:acm:us-east-1:631552345642:certificate/54ldsfga-4fd2-4264-955c-fsf3563346a2`.

Paste the certificate ARN into the `samconfig.toml` file. It needs to be placed in your `[<ENV>-public-access.deploy.parameters]` section, as the `parameter_overrides` value for the subkey `CertificateArn`. Keep that file open as you move on to the next section.

Change your AWS UI's region selection back from US East to the region into which you're deploying. The region selection is stored in browser cookies, so if you forget to do this then you *will* be confused for 5 minutes when resource you know you've created aren't visible in the UI!

### Preparing for deployment

In the `samconfig.toml` file, find the section you created earlier called `[<ENV>-public-access.deploy.parameters]`. Make sure you're in the `-public-access` deploy section variant: you copied 2 `deploy` sections, previously.

In this section, update the value of the `PublicFqdn` subkey inside the `parameter_overrides` setting. This should be the FQDN over which you're presenting the app.

Also make sure the `StackNameSuffix` subkey is set to the name you've given your deployment.

Now find the `[<ENV>.deploy.parameters]` section (*without* a `-public-access` component) and make sure the `parameter_overrides` setting subkey of `AppIsBehindCloudFront` is set to `True`. If it's not already set to True, you'll need to redeploy the Lambda app after setting it. Follow [the deployment instructions above](#deploying-the-built-artifacts]. This redeployment should take less than a minute as you don't need to rebuild (`sam build`) the deployment artifacts in this instance.

### Deploying DNS+TLS+CDN

With everything in place, you can now deploy. NB the `config-env` specified here *contains the `-public-access` suffix*.

This deployment will take **around** 5 minutes; subsequent deployments should take less time (if any!) so long as the CloudFront distribution isn't modified as part of the deployment. Given that price of an unused CloudFront distribution is effectively zero, there's no immediate need to tear the environment down from a cost perspective.

```
/code/aggregator-api$ pipenv run sam deploy --config-env jcm1-public-access

	Deploying with following values
	===============================
	Stack name                   : AggregatorApiPublicAccess-jcm1
	Region                       : eu-west-2
	Confirm changeset            : False
	Deployment s3 bucket         : None
	Capabilities                 : ["CAPABILITY_IAM"]
	Parameter overrides          : {'StackNameSuffix': 'jcm1', 'CertificateArn': 'arn:aws:acm:us-east-1:489559689862:certificate/5d0d7a82-4dd2-4264-955c-f9840701bfa2', 'PublicFqdn': 'jcm1.environments.womblelabs.co.uk'}
	Signing Profiles           : {}

Initiating deployment
=====================

Waiting for changeset to be created..

CloudFormation stack changeset
-------------------------------------------------------------------------------------------------------------------------------------
Operation                              LogicalResourceId                      ResourceType                           Replacement
-------------------------------------------------------------------------------------------------------------------------------------
+ Add                                  CloudFrontDistribution                 AWS::CloudFront::Distribution          N/A
+ Add                                  DnsRecord                              AWS::Route53::RecordSet                N/A
-------------------------------------------------------------------------------------------------------------------------------------

Changeset created successfully.
arn:aws:cloudformation:eu-west-2:489559689862:changeSet/samcli-deploy1607436164/07b0fbf8-0fff-4082-a880-e3ca03238bc6

2020-12-08 14:02:50 - Waiting for stack create/update to complete

CloudFormation events from changeset
-------------------------------------------------------------------------------------------------------------------------------------
ResourceStatus                         ResourceType                           LogicalResourceId                      ResourceStatusReason
-------------------------------------------------------------------------------------------------------------------------------------
CREATE_IN_PROGRESS                     AWS::CloudFront::Distribution          CloudFrontDistribution                 -
CREATE_IN_PROGRESS                     AWS::CloudFront::Distribution          CloudFrontDistribution                 Resource creation Initiated
CREATE_COMPLETE                        AWS::CloudFront::Distribution          CloudFrontDistribution                 -
CREATE_IN_PROGRESS                     AWS::Route53::RecordSet                DnsRecord                              -
CREATE_IN_PROGRESS                     AWS::Route53::RecordSet                DnsRecord                              Resource creation Initiated
CREATE_COMPLETE                        AWS::Route53::RecordSet                DnsRecord                              -
CREATE_COMPLETE                        AWS::CloudFormation::Stack             AggregatorApiPublicAccess-jcm1         -
-------------------------------------------------------------------------------------------------------------------------------------

CloudFormation outputs from deployed stack
--------------------------------------------------------------------------------------------------------------------------------------
Outputs
--------------------------------------------------------------------------------------------------------------------------------------
Key                 PublicFqdn
Description         The Aggregator API's URL.
Value               https://jcm1.environments.womblelabs.co.uk/

Key                 CloudFrontDistributionFqdn
Description         The FQDN of the CloudFront distribution serving this instance.
Value               d2yscou5nym8sl.cloudfront.net
--------------------------------------------------------------------------------------------------------------------------------------

Successfully created/updated stack - AggregatorApiPublicAccess-jcm1 in eu-west-2
```

### Testing the deployment

Use the pytests in `.circleci/tests/system/` to check the deployment is working as intended.

Teach the tests about your config env by setting both the `SAM_LAMBDA_CONFIG_ENV` and `SAM_PUBLIC_CONFIG_ENV` environment variables appropriately:

```
$ SAM_LAMBDA_CONFIG_ENV=jcm1 SAM_PUBLIC_CONFIG_ENV=jcm1-public-access pipenv run pytest -vrP --disable-warnings .circleci/tests/system/
========================================================== test session starts ==========================================================
platform linux -- Python 3.8.5, pytest-6.1.2, py-1.9.0, pluggy-0.13.1 -- /home/ubuntu/.local/share/virtualenvs/aggregator-api-_ak-AzJ8/bin/python
cachedir: .pytest_cache
django: settings: aggregator.settings.testing (from ini)
rootdir: /home/ubuntu/code/aggregator-api, configfile: pytest.ini
plugins: flakes-4.0.3, django-3.10.0, cov-2.10.1
collected 3 items

.circleci/tests/system/test_app_via_api_gateway.py::test_app_front_page_http_200 PASSED                                 [ 33%]
.circleci/tests/system/test_app_via_cloudfront.py::test_public_front_page_http_200 PASSED                               [ 66%]
.circleci/tests/system/test_app_via_cloudfront.py::test_cdn_front_page_http_200 PASSED                                  [100%]

================================================================ PASSES =================================================================
===================================================== 3 passed, 7 warnings in 0.56s =====================================================
```

## Tearing down deployments

Teardown is done by CloudFormation.

If you have deployed the DNS+TLS+CDN public-access stack, you **must** fully tear this stack down before deleting the app stack. In fact, CloudFormation won't allow you to delete the app stack whilst the public-access stack exists.

Either at the CLI using the `aws` command, or via [the AWS CloudFormation web UI](https://console.aws.amazon.com/cloudformation/home?region=eu-west-2), delete the public-access stack first, and then the app stack.

If you created a Hosted Zone in Route53, consider deleting it. It will cost DC $6/year if you don't, so probably only delete it if you're 99% sure you'll never stand up this environment again! If you **do** choose to delete it, tidy up by also deleting the NS records you added into the zone's parent zone. Be *very* sure only to delete the NS records with a name exactly matching the zone you created!

There is no ongoing cost (or initial cost) for any ACM certificates you created but, if the certificate is only valid for your domain and you've just deleted your domain, then it's only polite to take 15 seconds to tidy up and also delete the certificate in [the ACM US East web UI](https://console.aws.amazon.com/acm/home?region=us-east-1).
