[![CircleCI](https://circleci.com/gh/DemocracyClub/aggregator-api.svg?style=svg)](https://circleci.com/gh/DemocracyClub/aggregator-api)
[![Coverage Status](https://coveralls.io/repos/github/DemocracyClub/aggregator-api/badge.svg?branch=master)](https://coveralls.io/github/DemocracyClub/aggregator-api?branch=master)
![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)

# developers.democracyclub.org.uk API

## About

This project provides an API gateway in front of other Democracy Club APIs.

* The `/postcode` and `/address` APIs provide a nice abstraction over calling both the WDIV and WCIVF APIs and combine the responses.
* The `/elections` endpoint is a straight proxy for EE's `/elections` endpoint.
* The project hosts user-facing documentation for the API and sandbox outputs to help data consumers develop applications when real data is not available.
* As time goes on, developers.democracyclub.org.uk should become a one-stop-shop for DC data, additionally proxying additional EE/YNR endpoints.

## Local Development

### Application

* `cp aggregator-api/aggregator/settings/local.example.py aggregator-api/aggregator/settings/local.py`
* Install Python dependencies: `pipenv install --dev`
* Run the test suite: `pytest`
* Run lint checks: `pytest --flakes`
* Auto-format: `black .`

### Documentation

We build the docs locally instead of rendering on-the-fly and then commit the compiled documentation so it can be served as a static template. Compile the docs with `./manage.py build_docs`. The API docs use [drafter 3](https://github.com/apiaryio/drafter/) for parsing [API Blueprint](https://apiblueprint.org/). On linux this will be installed automatically with the python dependencies. On OSX/Windows, this needs to be [installed seperately](https://github.com/apiaryio/drafter/tree/v3.2.7#install).

## Configuration

### Local Settings

For local development, the only required setting is `SECRET_KEY`. In `local.py`, it may also be useful to set:

* `EE_BASE_URL` - e.g: to run against a local WDIV install instead of elections.democracyclub.org.uk
* `WCIVF_BASE_URL` - e.g: to run against a local WDIV install instead of whocanivotefor.co.uk
* `WDIV_BASE_URL` - e.g: to run against a local WDIV install instead of wheredoivote.co.uk
* `WDIV_API_KEY` - WDIV API key. In local dev, anonymous access is generally sufficient. You are unlikely to exceed the rate limit.

### Production Settings

In production, settings are obtained from environment variables. In production, we need:

* `SECRET_KEY` - Django secret key.
* `WDIV_API_KEY` - WDIV API key. For production usage, we must call WDIV with an API key to ensure we are not rate limited.
* `SENTRY_DSN` - If set, exceptions will be logged here.
* `ENV` - "prod" or "dev" - used by and sentry. FIXME: not currently propagated via the SAM CLI

## Deployment

* The API is hosted on AWS Lambda and built with [the AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/what-is-sam.html)
* Deployment of 3 parallel environments is [handled by Circle CI](/.circleci/config.yml#L188)
* If you merge to master and all the tests pass, deployments will be triggered:
   - to `development` and `staging` in parallel
   - to `production`, if `staging` smoke tests pass

### Development deployments to AWS Lambda

Development deployments are described in detail in [a separate document](/docs/new-development-deployment.md).

Here are the happy-path steps to deploy to DC's development AWS account. You *will* want to change the "mynewenv" deployment name to [one of your own choosing](/docs/new-development-deployment.md#setting-up-the-configuration-file)!

```shell
# export AWS_ACCESS_KEY_ID
# export AWS_SECRET_ACCESS_KEY
# export AWS_SESSION_TOKEN
git clone git@github.com:DemocracyClub/aggregator-api.git
cd aggregator-api
git checkout aws-ci-cd || true
pipenv install --dev --python $(cat .python-version | cut -f-2 -d.)
SBUC=""
docker run hello-world 2>/dev/null >/dev/null && SBUC='--use-container'
NEW_ENV_NAME=mynewenv pipenv run python samconfig.toml.d/new-dev-env.py >>samconfig.toml
[ ! -z $AWS_ACCESS_KEY_ID ] || { echo "You've forgotten to export the 3 AWS_* environment variables mentioned above!" ; read -p "Hit Ctrl-C, export them, and then continue from this point ... "; }
AWS_DEFAULT_REGION=eu-west-2 pipenv run sam validate
pipenv run make
pipenv run sam build  --config-env mynewenv ${SBUC}
pipenv run sam deploy --config-env mynewenv
# The function is (hopefully!) now deployed to Lambda.
# It's accessible via AWS API Gateway on the 'AggregatorApiFqdn' domain,
# mentioned a few lines above, when accessed on the path '/Prod'.

```

These steps should have deployed the app to Lambda.

You can continue and add TLS, caching, and a custom domain to this deployment by following [the rest of the deployment document](/docs/new-development-deployment.md#deploying-tls-cdn-and-dns-on-top-of-an-existing-lambda-deployment).
