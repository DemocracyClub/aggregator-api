from common.auth_models import User, UserDoesNotExist


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
    authentication = {"data": {"auth_token": api_key}}
    # TMP: disable dynamodb lookup for the time being
    # if not api_key:
    #     raise Exception("Unauthorized")
    #
    # authentication = dynamodb_auth(api_key)
    # if not authentication["authenticated"]:
    #     raise Exception("Unauthorized")

    return {
        "principalId": "sym",
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
