# New automated deployments from CircleCI

This process has been tested in the `development` env.

## In CircleCI and the AWS web UI

If required, create a new CircleCI deployment "Context". A good initial topology is one Context per AWS account. You'll find multiple existing Contexts to guide the new Context's naming.

If neccessary, create an AWS IAM user as per the [account setup document](/docs/new-aws-account-setup.md#users) and place the user's credentials as environment variables in the Context as described in that document.

Choose a long random string and place it in the Context as the `SECRET_KEY` environment variable. Avoid including any shell metacharacters, eg.`$*;"'`. Avoid backticks, too!

Create a domain in the AWS account as per [the development deployment document](/docs/new-development-deployment.md#create-a-domain). Make sure to also [delegate it correctly from its parent domain](/docs/new-development-deployment.md#delegate-dns-authority-to-your-new-domain). For important deployments, increase the NS TTL value mentioned in that document to a day or longer. Ignore the document's instructions to save the domain in the `samconfig.toml` config file. Instead, save the domain in the CircleCI Context as the environment variable `PUBLIC_FQDN`.

Create a TLS certificate in the AWS account as per [the development deployment document](/docs/new-development-deployment.md#find-the-acm-arn-of-a-certificate-thats-valid-for-your-domain).

When choosing between creating a single-domain or wildcard certificate, consider if other operators may be creating multiple Aggregator API deployments under the same parent domain as your chosen FQDN. If so, creating a wildcard certificate (for `*.parent.domain.tld`) may be the better choice. Reasons *not* to do this are minimal: primarily they're around not having an overly-"powerful" certificate provisioned and available for use (and abuse) if it's not required or useful.

Ignore the document's instructions to save the certificate's ARN in the `samconfig.toml` config file. Instead, save the domain in the CircleCI Context as the environment variable `CERTIFICATE_ARN`.

## In the Aggregator API codebase

### In `.circleci/config.yml`

Clone the staging or production `sam_deploy` workflow job and alter the keys as appropriate. You'll definitely need to amend `name` and `dc-environment`.

Change `context` to the name of the new Context you created above, if you created one. If you're deploying into an already-deployed-into-by-Circle AWS account, reuse the existing Context.

You may want to change the `requires` prerequisites to change this deployment's prerequisites.

Add the `dc-environment` name to `sam_deploy`'s `dc-environment` enum, but consider changing the enum to merely be an arbitary string if doing this last step frequently proves to be annoying.

### In `samconfig.toml.d/`

Copy one of the `ci-*.yml` files and name it `ci-<env>.yml`, where `<env>` is the `dc-environment` setting already entered in `.circleci/config.yml`.

In the new file `samconfig.toml.d/ci-<env>.yml`, replace all instances of the cloned environment's name with whatever value you've chosen for `<env>`.

NB the `s3_bucket` setting is *per-AWS account*, so you should make sure it matches the name of the already-created (as per the [AWS account setup document](docs/new-aws-account-setup.md#s3-buckets)) deployment-assets bucket in the AWS account.

Commit and push all the changes you've made, and CI should deploy your new enviroment.

A new environment takes under 10 minutes to deploy, most of which is CloudFormation creating the CloudFront CDN distribution. If the CircleCI job times out (the default timeout is 10 minutes, which has not been observed being exceeded), check the CloudFormation Stack's progress in [the AWS web UI](https://console.aws.amazon.com/cloudformation) before re-running the job. It may be that the Stack is still being created, and runs to the end successfully, in which case a job rerun will also succeed.

However, if the Stack has failed to create and is in a "CREATE_FAILED" state then you'll have to manually delete the Stack in the UI before rerunning the CircleCI job. This is an intentional CloudFormation feature that allows you to view the underlying reason that Stack creation failed, and fix it, before deleting the Stack and losing that failure-related insight. See [the AWS docs](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-describing-stacks.html#w2ab1c23c15c17c11) for more information on potential failure causes.
