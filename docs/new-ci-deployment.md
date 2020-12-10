# New automated deployments from CircleCI

* [In CircleCI and the AWS web UI](#in-circleci-and-the-aws-web-ui)
* [In the Aggregator API codebase](#in-the-aggregator-api-codebase)
   * [In .circleci/config.yml](#in-circleciconfigyml)
   * [In samconfig.toml.d/](#in-samconfigtomld)
* [Debugging CI failures](#debugging-ci-failures)
   * [Viewing CI-managed deployment's logs](#viewing-ci-managed-deployments-logs)
   * [CircleCI masks environment variables' values](#circleci-masks-environment-variables-values)
   * [Deployment jobs show you their deployment variables](#deployment-jobs-show-you-their-deployment-variables)

This process has been tested in the `development` and `production` environments.

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

## Debugging CI failures

A common cause of problems is environment variables. You might have entered them subtly wrongly, or some part of the CI process might be distorting or passing them around in a modified form - but this is most likely to be the deployment scripts, not behind-the-scenes CircleCI breakage.

Here are some techniques for figuring out if you've encountered any of these kinds of problems.

### Viewing CI-managed deployment's logs

Just as [developer deployments' logs can be accessed using the `sam` CLI](/docs/new-development-deployment.md#viewing-app-logs), so too can CI-managed deployments' logs.

In order to access these logs, first [set up your local environment](/docs/new-development-deployment.md#example-output-and-aws-credentials) with access to the AWS account which contains the deployment.

Next, identify the config file inside `samconfig.toml.d` that CI uses to manage the deployment.

Fianlly, access the logs by pointing the `sam` CLI towards the config file and, within that file, to the config env it should use:

```
~/code/aggregator-api$ pipenv run sam logs --config-file samconfig.toml.d/ci-staging.toml --config-env staging
[ ... some logs ... ]
```

### CircleCI masks environment variables' values

Once you've inserted an environment variable into CircleCI's per-project or per-Context settings, it won't allow that string to be echoed during test/build/deploy/etc workflows. You can think of the CircleCI product as wrapping the entire output of all executed jobs and workflows in a big `sed` wrapper that looks for the variables' values and swaps them out for asterisks. They describe the feature [on their blog](https://circleci.com/blog/keep-environment-variables-private-with-secret-masking/), and mention a few "gotchas":

- Secrets below 4 characters will not be masked.
- Secrets with the values true, TRUE, false, FALSE will not be masked.
- This does not prevent secrets from being displayed when you SSH into a build.

Presumably the 4-character limit is because, otherwise, if one created a variable with the value "a", then the entire CI output would become increasingly useless, being littered with single-character redactions wherever an "a" was output!

One way to use this feature for debugging is to look at the outputs of your jobs where you might expect non-secrets that are stored as environment variables (e.g. FQDNs, debug settings, etc) and are echoed during deployment. If the values are **not** masked, then your expectation of what's in the environment variable might not match what's actually there.

### Deployment jobs show you their deployment variables

In this project's CircleCI configuration file, liberal use is made of `printenv`, which is a safe way of printing environment variables: [circleci/config.yml#L101](circleci/config.yml#L101). Notice that this is used in 3 different ways:

1. Environment variables which are synthesied or set inside a CircleCI job (e.g. `DJANGO_SETTINGS_MODULE` in the above link) can be printed directly. They aren't secret, or even sensitive, and because they're not stored in CircleCI they won't be masked.
1. Non-secret, but semi-sensitive variables that are held in CircleCI (e.g. `PUBLIC_FQDN`) are `printenv`'d and then uppercased, so that the values can be seen, but without being masked (as they're no longer identical to the value that the CircleCI redaction system is searching for).
1. Secrets such as API keys have their values hashed and printed. You can run the hash locally, on your known-good string, to check that the hashes match and the CI system is actually using the value you believe it's using.

Note that `printenv` isn't a substitute for `echo`, which is able to construct arbitrary strings containing environment variables. The only job that `printenv` does is to take environment variable **names** as arguments, output their values (one per line), and exit with an error code if any of the requested environment variables aren't found. For a *safer* mechanism than using `echo` to do arbitrary string construction using shell environment variables, consider using the shell builtin `printf` instead.
