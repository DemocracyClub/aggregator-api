import sys

sys.path.append("api")

from common.auth_models import User, UserDoesNotExist  # noqa
from common.sentry_helper import init_sentry  # noqa

init_sentry()


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

    authentication = dynamodb_auth(api_key)
    if not authentication["authenticated"]:
        raise Exception("Unauthorized")

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


if __name__ == "__main__":
    event = {
        "resource": "/",
        "path": "/",
        "httpMethod": "GET",
        "requestContext": {
            "resourcePath": "/",
            "httpMethod": "GET",
            "path": "/Prod/",
        },
        "headers": {
            "accept": "text/html",
            "accept-encoding": "gzip, deflate, br",
            "Host": "xxx.us-east-2.amazonaws.com",
            "User-Agent": "Mozilla/5.0",
        },
        "multiValueHeaders": {
            "accept": ["text/html"],
            "accept-encoding": ["gzip, deflate, br"],
        },
        "queryStringParameters": {"auth_token": "foo"},
        "multiValueQueryStringParameters": None,
        "pathParameters": None,
        "stageVariables": None,
        "body": None,
        "isBase64Encoded": False,
    }

    print(lambda_handler(event, None))
