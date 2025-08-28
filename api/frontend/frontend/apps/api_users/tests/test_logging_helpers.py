import csv
from io import StringIO

import boto3
import pytest
from api_users.logging_helpers import APIKeyForLogging
from api_users.models import APIKey
from django.contrib.auth import get_user_model
from django.test.utils import override_settings
from moto import mock_aws


@pytest.fixture
def api_key_data():
    return {
        "key": "1234567890",
        "key_name": "test-key",
        "user_name": "test-user",
        "email": "test@example.com",
        "usage_reason": "Testing purposes",
    }


@pytest.fixture
def api_key(api_key_data):
    return APIKeyForLogging(**api_key_data)


@pytest.fixture
def s3_client():
    with mock_aws():
        yield boto3.client("s3", region_name="eu-west-2")


@pytest.fixture
def s3_dev_bucket(s3_client):
    s3_client.create_bucket(
        Bucket="dc-monitoring-dev-logging",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )


@pytest.fixture
def s3_prod_bucket(s3_client):
    s3_client.create_bucket(
        Bucket="dc-monitoring-production-logging",
        CreateBucketConfiguration={"LocationConstraint": "eu-west-2"},
    )


@pytest.fixture
@pytest.mark.django_db
def user_fixture():
    User = get_user_model()
    return User.objects.create(
        email="test@example.com",
        name="Tester",
        api_plan="hobbyists",
    )


@pytest.fixture
@pytest.mark.django_db
def api_key_fixture(user_fixture):
    return APIKey.objects.create(
        name="Test API Key",
        usage_reason="Testing purposes",
        key="api_key_12345678",
        is_active=True,
        rate_limit_warn=False,
        key_type="development",
        user=user_fixture,
    )


def test_file_name(api_key):
    assert api_key.file_name == "1234_7890.csv"


@pytest.mark.parametrize(
    "env,expected",
    [
        ("production", "api-users/aggregator-api/latest/"),
        ("development", "api-users/aggregator-api/development/latest/"),
        ("staging", "api-users/aggregator-api/staging/latest/"),
        (None, "api-users/aggregator-api/local-dev/latest/"),
        ("other", "api-users/aggregator-api/local-dev/latest/"),
    ],
)
def test_prefix(api_key, env, expected):
    with override_settings(DC_ENVIRONMENT=env):
        assert api_key.prefix == expected


@pytest.mark.parametrize(
    "env,expected",
    [
        ("production", "dc-monitoring-production-logging"),
        ("development", "dc-monitoring-dev-logging"),
        ("staging", "dc-monitoring-dev-logging"),
        (None, "local-dev-logging"),
        ("other", "local-dev-logging"),
    ],
)
def test_bucket(api_key, env, expected):
    with override_settings(DC_ENVIRONMENT=env):
        assert api_key.bucket == expected


@pytest.mark.parametrize("env", ["production", "development", "staging"])
def test_upload_to_s3_deployed(
    api_key, s3_client, s3_prod_bucket, s3_dev_bucket, env, caplog
):
    with override_settings(DC_ENVIRONMENT=env), mock_aws():
        # Upload the file
        destination = api_key.upload_to_s3()
        expected_destination = (
            f"s3://{api_key.bucket}/{api_key.prefix}{api_key.file_name}"
        )

        assert destination == expected_destination
        assert f"Uploaded csv to {expected_destination}" in caplog.text

        # Verify the file was uploaded to S3
        s3_response = s3_client.get_object(
            Bucket=api_key.bucket, Key=f"{api_key.prefix}{api_key.file_name}"
        )
        content = s3_response["Body"].read().decode("utf-8")

    # Parse the CSV content
    csv_reader = csv.reader(StringIO(content))
    rows = list(csv_reader)

    # Verify only one row is returned
    assert len(rows) == 1, "CSV should contain exactly one row"

    # Verify the row content matches our input
    row = rows[0]
    assert row[0] == api_key.key
    assert row[1] == api_key.key_name
    assert row[2] == api_key.user_name
    assert row[3] == api_key.email
    assert row[4] == api_key.usage_reason


def test_upload_to_s3_local(api_key, caplog):
    with override_settings(DC_ENVIRONMENT=None):
        destination = api_key.upload_to_s3()
    expected_destination = (
        f"s3://{api_key.bucket}/{api_key.prefix}{api_key.file_name}"
    )

    assert destination == expected_destination
    assert f"Not uploading to {expected_destination}" in caplog.text


@pytest.mark.django_db()
def test_from_django_model(user_fixture, api_key_fixture):
    api_key_for_logging = APIKeyForLogging.from_django_model(api_key_fixture)

    # Assert that the properties are correctly set
    assert api_key_for_logging.key == "api_key_12345678"
    assert api_key_for_logging.key_name == "Test API Key"
    assert api_key_for_logging.user_name == "Tester"
    assert api_key_for_logging.email == "test@example.com"
    assert api_key_for_logging.usage_reason == "Testing purposes"
