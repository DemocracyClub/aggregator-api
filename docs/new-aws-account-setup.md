# Setting up an AWS account for Aggregator API deployments

* [IAM Entities](#iam-entities)
   * [Policies](#policies)
      * [AggregatorApiDeployer](#aggregatorapideployer)
      * [AggregatorApiPublicAccessDeployer](#aggregatorapipublicaccessdeployer)
   * [Roles](#roles)
      * [AggregatorApiLambdaExecutionRole](#aggregatorapilambdaexecutionrole)
   * [Groups](#groups)
      * [AggregatorApiDeployers](#aggregatorapideployers)
   * [Users](#users)
      * [CircleCI](#circleci)
* [S3 buckets](#s3-buckets)
   * [Deployment artifact bucket](#deployment-artifact-bucket)

This document describes the setup that an AWS account requires in order to have the Aggregator API deployed into it. This does not deal with the deployment of the API itself, but instead the per-account prerequisites that need to exist in order to support developer- and CI-originated deployments.

## IAM Entities

In [the AWS IAM web UI](https://console.aws.amazon.com/iam) create the following entities:

### Policies

#### AggregatorApiDeployer

Create an IAM Policy named `AggregatorApiDeployer`.

Set its description as `Allows deployment of the Aggregator API service`.

Set its Policy document as follows: **FIXME: can the Resources be scoped with account as IAM variables?**

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "apigateway:DELETE",
                "apigateway:GET",
                "apigateway:PATCH",
                "apigateway:POST",
                "apigateway:PUT",
                "cloudformation:CreateChangeSet",
                "cloudformation:DescribeChangeSet",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStacks",
                "cloudformation:ExecuteChangeSet",
                "cloudformation:GetTemplateSummary",
                "lambda:AddPermission",
                "lambda:CreateAlias",
                "lambda:CreateFunction",
                "lambda:DeleteAlias",
                "lambda:DeleteFunction",
                "lambda:GetFunction",
                "lambda:GetFunctionConfiguration",
                "lambda:GetLayerVersion",
                "lambda:ListTags",
                "lambda:ListVersionsByFunction",
                "lambda:PublishLayerVersion",
                "lambda:PublishVersion",
                "lambda:RemovePermission",
                "lambda:TagResource",
                "lambda:UntagResource",
                "lambda:UpdateAlias",
                "lambda:UpdateFunctionCode",
                "lambda:UpdateFunctionConfiguration",
                "logs:CreateLogGroup",
                "logs:PutRetentionPolicy",
                "s3:AbortMultipartUpload",
                "s3:GetObject",
                "s3:ListBucketMultipartUploads",
                "s3:ListMultipartUploadParts",
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:PutObjectTagging"
            ],
            "Resource": [
                "arn:aws:apigateway:eu-west-2:*:/restapis",
                "arn:aws:apigateway:eu-west-2:*:/restapis/*",
                "arn:aws:cloudformation:eu-west-2:*:changeSet/samcli-deploy*/*",
                "arn:aws:cloudformation:eu-west-2:*:stack/AggregatorApiApp-*/*",
                "arn:aws:cloudformation:eu-west-2:aws:transform/Serverless-2016-10-31",
                "arn:aws:lambda:eu-west-2:*:function:AggregatorApiApp-*",
                "arn:aws:lambda:eu-west-2:*:layer:DependenciesLayer",
                "arn:aws:lambda:eu-west-2:*:layer:DependenciesLayer:*",
                "arn:aws:logs:eu-west-2:*:log-group:/aws/lambda/AggregatorApiApp-*",
                "arn:aws:s3:::aggregator-api-deployment-artifacts-*",
                "arn:aws:s3:::aggregator-api-deployment-artifacts-*/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": "iam:PassRole",
            "Resource": [
                "arn:aws:iam::*:role/AggregatorApiLambdaExecutionRole"
            ],
            "Condition": {
                "StringEquals": {
                    "iam:PassedToService": "lambda.amazonaws.com"
                }
            }
        }
    ]
}
```

#### AggregatorApiPublicAccessDeployer

Create an IAM Policy named `AggregatorApiPublicAccessDeployer`.

Set its description as `Allows SAM CLI deployment of the CDN+DNS which provide public access to the Aggregator API`.

Set its Policy document as follows: **FIXME: can the Resources be scoped with accounts as IAM variables?**

```
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "route53:ListHostedZones"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "cloudformation:CreateChangeSet",
                "cloudformation:DescribeChangeSet",
                "cloudformation:DescribeStackEvents",
                "cloudformation:DescribeStacks",
                "cloudformation:ExecuteChangeSet",
                "cloudformation:GetTemplateSummary",
                "cloudfront:CreateDistribution",
                "cloudfront:DeleteDistribution",
                "cloudfront:GetDistribution",
                "cloudfront:TagResource",
                "cloudfront:UpdateDistribution",
                "route53:ChangeResourceRecordSets",
                "route53:GetChange",
                "route53:ListResourceRecordSets",
                "s3:AbortMultipartUpload",
                "s3:GetObject",
                "s3:ListBucketMultipartUploads",
                "s3:ListMultipartUploadParts",
                "s3:PutObject",
                "s3:PutObjectAcl",
                "s3:PutObjectTagging"
            ],
            "Resource": [
                "arn:aws:cloudformation:eu-west-2:*:stack/AggregatorApiPublicAccess-*/*",
                "arn:aws:cloudformation:eu-west-2:*:changeSet/samcli-deploy*/*",
                "arn:aws:cloudformation:eu-west-2:aws:transform/Serverless-2016-10-31",
                "arn:aws:cloudfront::*:distribution/*",
                "arn:aws:route53::*:hostedzone/*",
                "arn:aws:route53::*:change/*",
                "arn:aws:s3:::aggregator-api-deployment-artifacts-*",
                "arn:aws:s3:::aggregator-api-deployment-artifacts-*/*"

            ]
        }
    ]
}
```

### Roles

#### AggregatorApiLambdaExecutionRole

Create an IAM role named `AggregatorApiLambdaExecutionRole`.

During creation:

- Select the use-case creation shortcut for Lambda
- Attach the AWS-managed policy: `AWSLambdaBasicExecutionRole`
- Tag the Role:
   - `dc-environment`: as appropriate
   - `dc-product`: `aggregator-api`
- Add the description: `Allows the Aggregator API to call other AWS services`.

After creation, ensure the trust relationship looks like this:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

### Groups

#### AggregatorApiDeployers

Create an IAM Group named `AggregatorApiDeployers`.

During creation:
- Attach the DC-managed policies:
   - `AggregatorApiDeployer`
   - `AggregatorApiPublicAccessDeployer`

### Users

#### CircleCI

Add an IAM User named `CircleCI`.

During creation:

- Select "Programmatic access" only.
- Add them to the group `AggregatorApiDeployers`
- Tag the user:
   - `dc-environment`: as appropriate
   - `dc-product`: `aggregator-api`

After creation, copy the generated access key ID and secret access key, and paste them inside an appropriately-named CircleCI "Context", with each value stored under its relevant standard [AWS environment variable name](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-envvars.html).

**Make very, *very* sure that you capture the key ID and secret precisely! Ensure that, when you paste it into the CircleCI UI, you don't accidentally insert any leading or trailing whitespace, and that you've copied the entire string each time - even if the string contains word-break characters that stop your browser from selecting the whole string!**

CircleCI Contexts have the concept of "Security Groups". We're not using them, yet, but they do merit some future investigation.

## S3 buckets

### Deployment artifact bucket

In the [AWS S3 web UI](https://s3.console.aws.amazon.com/s3/home?region=eu-west-2), create an S3 bucket.

- Name: `aggregator-api-deployment-artifacts-<environment>-<several-random-characters>`
- Region: Wherever you're deploying the Aggregator API; probably eu-west-2
- Public access: entirely disabled
- Versioning: disabled
- Tags:
   - `dc-environment`: as appropriate
   - `dc-product`: `aggregator-api`
- Encryption: doesn't matter

After creation, view the bucket and select the "Management" tab.

Select "Create lifecycle rule".

- Rule name: `delete-any-file-1-day-after-upload`
- Apply to all objects
- Tick the options for:
   - "Expire current versions of objects"
   - "Delete expired delete markers or incomplete multipart uploads"
- For "Expire current versions of objects":
   - Enter "1" day
- For "Delete expired delete markers or incomplete multipart uploads":
   - Tick "Delete incomplete multipart uploads"
   - Enter "1" day

Create the rule.
