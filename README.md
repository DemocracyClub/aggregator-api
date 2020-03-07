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

We build the docs locally instead of rendering on-the-fly and then commit the compiled documentation so it can be served as a static template. Compile the docs with `./manage.py build_docs`.

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
* `ENV` - "prod" or "dev" - used by deploy script and sentry.

## Deployment

* The API is hosted on AWS Lambda and built with zappa
* Deployment is handled by Circle CI: https://github.com/DemocracyClub/aggregator-api/blob/44d9b39fd32737e7f68d1019d14fbd932f7bb41a/.circleci/config.yml#L67
* If you merge to master and all the tests pass, a deploy will be triggered
