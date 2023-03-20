from common.auth_models import User
from starlette.datastructures import Headers, QueryParams
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


class ForwardedForMiddleware:
    def __init__(
        self,
        app,
    ):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            headers = Headers(scope=scope)
            forwarded_for = (
                headers.get("x-forwarded-host", "").split(":")[0].encode()
            )
            if forwarded_for:
                for i, header in enumerate(scope["headers"]):
                    if header[0] == b"host":
                        scope["headers"].pop(i)
                scope["headers"].append((b"host", forwarded_for))
        await self.app(scope, receive, send)


class UTMParamsMiddleware:
    """
    Pull any UTM tracking params from the querystring and attach them to the
    scope for use later.

    This saves parsing the querystring in each view, and standardises the
    use of UTM params.
    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        utm_dict = {}
        params = QueryParams(scope.get("query_string"))

        utm_dict["utm_source"] = params.get("utm_source")
        utm_dict["utm_campaign"] = params.get("utm_campaign")
        utm_dict["utm_medium"] = params.get("utm_medium")

        scope["utm_dict"] = utm_dict
        await self.app(scope, receive, send)


class APIGatewayAuthenticatorContextMiddleware:
    """
    Some app functions are behind an AWS API Gateway Authorizer.

    The Authorizer will control access to the Lambdas functions "behind" it,
    and will also insert context data about the authenticated user.

    We want to use this data when logging access, so this middleware parses the
    context in to a User model that can be used by functions.

    There are two other cases to consider:

    1. When we're on AWS Lambda but running an unauthenticated function.
       We don't know who the user is in this case, so we can just create a fake user
    2. When we're not on AWS Lambda, like when running tests or local dev.

    """

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        aws_event = scope.get("aws.event", {})
        authorizer_data = aws_event.get("requestContext", {}).get(
            "authorizer", {}
        )

        if authorizer_data:
            # We've been passed through an authorizer so we can create a User model
            user = User.from_authorizer_data(authorizer_data)
        elif aws_event:
            # We're on AWS Lambda, but this isn't a function with an authorizer
            user = User(
                user_id="unauthenticated_user", api_key="unauthenticated_user"
            )
        else:
            # We're not on AWS Lambda
            user = User(user_id="direct_access", api_key="local-dev")

        scope["api_user"] = user
        await self.app(scope, receive, send)


MIDDLEWARE = [
    Middleware(ForwardedForMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_headers=["Token", "Origin", "X-Requested-With"],
    ),
    Middleware(UTMParamsMiddleware),
    Middleware(APIGatewayAuthenticatorContextMiddleware),
]
