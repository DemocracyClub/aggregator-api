import os

import boto3
import pytest
from moto import mock_dynamodb
from mypy_boto3_dynamodb import DynamoDBServiceResource

from api_auth.handler import dynamodb_auth
from common.auth_models import User


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
    assert resp["authenticated"] == True
    assert resp["data"]["user_id"] == "1"


def test_auth_incorrect_key(dynamodb):
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] == False


def test_auth_inactive_key(dynamodb):
    user = User(api_key="12345", user_id="1", is_active=False)
    user.save()
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] == False
    assert resp["data"]["is_active"] == False


def test_auth_rate_limit_warn(dynamodb):
    user = User(api_key="12345", user_id="1", rate_limit_warn=True)
    user.save()
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] == True
    assert resp["warnings"] == ["Rate limit exceeded"]


def test_auth_delete_user(dynamodb):
    user = User(api_key="12345", user_id="1", rate_limit_warn=True)
    user.save()
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] == True
    user.delete()
    resp = dynamodb_auth("12345")
    assert resp["authenticated"] == False
    assert resp["error"] == "API key not found"
