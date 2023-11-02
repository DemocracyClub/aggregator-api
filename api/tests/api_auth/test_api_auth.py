import os

import boto3
import pytest
from api_auth.handler import dynamodb_auth, lambda_handler
from common.auth_models import User
from moto import mock_dynamodb
from mypy_boto3_dynamodb import DynamoDBServiceResource


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_REGION"] = "eu-west-2"
    os.environ.pop("AWS_PROFILE", None)


@pytest.fixture(scope="function")
def dynamodb(aws_credentials):
    with mock_dynamodb():
        db_client: DynamoDBServiceResource = boto3.resource(
            "dynamodb", region_name="eu-west-2"
        )
        keys = [
            {"AttributeName": "api_key", "KeyType": "HASH"},
        ]
        defs = [
            {"AttributeName": "api_key", "AttributeType": "S"},
        ]

        db_client.create_table(
            TableName="users",
            KeySchema=keys,
            AttributeDefinitions=defs,
            BillingMode="PAY_PER_REQUEST",
        )

        yield db_client


def test_auth_active_key(dynamodb):
    user = User(api_key="12345", user_id="1")
    user.save()
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] is True
    assert resp["data"]["user_id"] == "1"


def test_auth_incorrect_key(dynamodb):
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] is False


def test_auth_inactive_key(dynamodb):
    user = User(api_key="12345", user_id="1", is_active=False)
    user.save()
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] is False
    assert resp["data"]["is_active"] is False


def test_auth_rate_limit_warn(dynamodb):
    user = User(api_key="12345", user_id="1", rate_limit_warn=True)
    user.save()
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] is True
    assert resp["warnings"] == ["Rate limit exceeded"]


def test_auth_delete_user(dynamodb):
    user = User(api_key="12345", user_id="1", rate_limit_warn=True)
    user.save()
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] is True
    user.delete()
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] is False
    assert resp["error"] == "API key not found"


def test_lambda_no_api_key(dynamodb):
    from api_auth import handler

    handler.USE_DYNAMODB_AUTH = True
    # No auth_token key provided
    with pytest.raises(Exception) as e:
        lambda_handler({"queryStringParameters": {}}, {})
    assert str(e.value) == "Unauthorized"

    # Key provided, no value
    with pytest.raises(Exception) as e:
        lambda_handler({"queryStringParameters": {"auth_token": None}}, {})
    assert str(e.value) == "Unauthorized"

    # Key provided, with value, but not a valid key
    with pytest.raises(Exception) as e:
        lambda_handler({"queryStringParameters": {"auth_token": "12345"}}, {})
    assert str(e.value) == "Unauthorized"


def test_from_dynamodb(dynamodb):
    user = User(api_key="12345", user_id="1")
    user.save()
    user = User.from_dynamodb(api_key="12345")
    assert user.user_id == "1"
    assert user.rate_limit_warn is False
