import pytest
from starlette.testclient import TestClient
from voting_information.app import app as voting_information_app


@pytest.fixture(scope="function")
def vi_app_client() -> TestClient:
    with TestClient(app=voting_information_app) as client:
        yield client


@pytest.fixture(scope="function")
def mangum_app_client():
    """
    Use when testing the Mangum integration. Useful when testing
    in a more Lambda-like environment (e.g when testing Middleware)
    """

    def _request(handler, url):
        return handler(make_context_for_url(url), None)

    return _request


def make_context_for_url(url):
    """
    Makes an AWS-like HTTP context for Mangum.
    """

    return {
        "resource": url,
        "path": url,
        "httpMethod": "GET",
        "requestContext": {
            "resourcePath": url,
            "httpMethod": "GET",
            "path": f"/Prod{url}",
        },
        "headers": {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
            "accept-encoding": "gzip, deflate, br",
            "Host": "70ixmpl4fl.execute-api.us-east-2.amazonaws.com",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.132 Safari/537.36",
            "X-Amzn-Trace-Id": "Root=1-5e66d96f-7491f09xmpl79d18acf3d050",
        },
        "multiValueHeaders": {
            "accept": [
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
            ],
            "accept-encoding": ["gzip, deflate, br"],
        },
        "queryStringParameters": None,
        "multiValueQueryStringParameters": None,
        "pathParameters": None,
        "stageVariables": None,
        "body": None,
        "isBase64Encoded": False,
    }
