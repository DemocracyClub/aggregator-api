import os

import boto3
import pytest
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
def dynamodb(aws_credentials, settings):
    with mock_dynamodb():
        settings.USE_DYNAMODB = True

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
