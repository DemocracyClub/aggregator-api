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

    api_key = event["queryStringParameters"].get("auth_token", None)
    if not api_key:
        raise Exception("Unauthorized")

    authentication = dynamodb_auth(api_key)
    if not authentication["authenticated"]:
        raise Exception("Unauthorized")

    return {
        "principalId": "sym",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "execute-api:Invoke", "Effect": "Allow", "Resource": "*"}
            ],
        },
        "context": authentication["data"],
    }
