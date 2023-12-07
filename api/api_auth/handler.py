import os
import sys

sys.path.append("api")

from common.auth_models import User, UserDoesNotExist  # noqa
from common.sentry_helper import init_sentry  # noqa

init_sentry()

USE_DYNAMODB_AUTH = os.environ.get("USE_DYNAMODB_AUTH", False) in [
    True,
    "true",
    "True",
    "TRUE",
]
ENFORCE_AUTH = True


def dynamodb_auth(api_key: str, region_name="eu-west-2"):
    ret = {
        "authenticated": False,
        "error": None,
        "warnings": [],
        "data": {},
    }
    try:
        user = User.from_dynamodb(api_key)
    except UserDoesNotExist:
        ret["error"] = "API key not found"
        return ret
    ret.update({"data": user.as_dict()})
    if user.is_active:
        ret["authenticated"] = True
    else:
        ret["error"] = "API key not active"
    if user.rate_limit_warn:
        ret["warnings"].append("Rate limit exceeded")

    return ret


def lambda_handler(event, context):
    if "auth_token" not in event["queryStringParameters"]:
        raise Exception("Unauthorized")
    api_key = event["queryStringParameters"].get("auth_token", None)

    if not api_key:
        print("No API key provided")
        raise Exception("Unauthorized")

    if USE_DYNAMODB_AUTH:
        authentication = dynamodb_auth(api_key)
        if not authentication["authenticated"]:
            if ENFORCE_AUTH:
                raise Exception("Unauthorized")
            print(
                f"AUTH_ERROR: Would have raised 'Unauthorized' for key {api_key} but the Authorizer isn't enforced at the moment. Authorizing anyway"
            )
            authentication = {
                "data": {"user_id": api_key},
                "authenticated": True,
                "error": None,
                "warnings": [],
            }

    else:
        authentication = {
            "data": {"user_id": api_key},
            "authenticated": True,
            "error": None,
            "warnings": [],
        }

    return {
        "principalId": authentication["data"]["user_id"],
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "execute-api:Invoke",
                    "Effect": "Allow",
                    "Resource": "*",
                }
            ],
        },
        "context": authentication["data"],
    }
