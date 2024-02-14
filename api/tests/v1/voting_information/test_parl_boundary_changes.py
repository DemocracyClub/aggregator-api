import os
from unittest.mock import patch

import boto3
import httpx
import pytest
from common.settings import PARL_BOUNDARY_CHANGES_ENABLED
from elections_api_client import wcivf_ballot_cache_url_from_ballot
from moto import mock_aws
from tests.helpers import fixture_map, load_fixture

BUCKET_NAME = "addressbase-lookups.development"


@pytest.fixture()
def sample_postcode_data():
    yield [
        {
            "uprn": 10003707532,
            "address": "HARLOW STUDY CENTRE, WATERHOUSE MOOR, HARLOW",
            "postcode": "CM18 6BW",
            "outcode": "CM18",
            "current_constituencies_official_identifier": "gss:E14000729",
            "current_constituencies_name": "Harlow",
            "new_constituencies_official_identifier": "gss:E14001267",
            "new_constituencies_name": "Harlow",
        },
        {
            "uprn": 100090549541,
            "address": "208 WATERHOUSE MOOR, HARLOW",
            "postcode": "CM18 6BW",
            "outcode": "CM18",
            "current_constituencies_official_identifier": "gss:E14000729",
            "current_constituencies_name": "Harlow",
            "new_constituencies_official_identifier": "gss:E14001267",
            "new_constituencies_name": "Harlow",
        },
    ]


@pytest.fixture(scope="function")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture()
def mock_s3_select(aws_credentials):
    with mock_aws():
        client = boto3.client("s3")
        client.create_bucket(Bucket=BUCKET_NAME)
        yield client


@pytest.fixture()
def mock_wdiv(respx_mock):
    input_fixture = fixture_map["AA12AA"]
    fixture = load_fixture(input_fixture, "wdiv")
    respx_mock.get("https://wheredoivote.co.uk/api/beta/postcode/AA12AA/").mock(
        return_value=httpx.Response(
            200,
            json=fixture,
        )
    )

    for ballot in fixture["ballots"]:
        respx_mock.get(
            wcivf_ballot_cache_url_from_ballot(ballot["ballot_paper_id"])
        ).mock(
            return_value=httpx.Response(
                200,
                json=load_fixture(input_fixture, ballot["ballot_paper_id"]),
            )
        )


@pytest.fixture()
def mock_s3_select_postcode_response():
    with patch(
        "parl_boundary_changes.client.ParlBoundaryChangeApiClient.get_data_for_postcode"
    ) as mock_method:
        yield mock_method


@pytest.mark.skipif(
    not PARL_BOUNDARY_CHANGES_ENABLED, reason="Parl boundary feature disabled"
)
def test_parl_boundary_postcode_no_s3_data(
    mock_s3_select, vi_app_client, mock_wdiv
):
    resp = vi_app_client.get("/api/v1/postcode/AA12AA/")
    assert resp.json()["parl_boundary_changes"] is None


@pytest.mark.skipif(
    not PARL_BOUNDARY_CHANGES_ENABLED, reason="Parl boundary feature disabled"
)
def test_parl_boundary_postcode_no_address_picker(
    mock_s3_select_postcode_response,
    vi_app_client,
    mock_wdiv,
    sample_postcode_data,
):
    mock_s3_select_postcode_response.return_value = sample_postcode_data

    resp = vi_app_client.get("/api/v1/postcode/AA12AA/")
    assert resp.json()["parl_boundary_changes"] == {
        "CHANGE_TYPE": "BOUNDARY_CHANGE",
        "current_constituencies_name": "Harlow",
        "current_constituencies_official_identifier": "gss:E14000729",
        "new_constituencies_name": "Harlow",
        "new_constituencies_official_identifier": "gss:E14001267",
    }


@pytest.mark.skipif(
    not PARL_BOUNDARY_CHANGES_ENABLED, reason="Parl boundary feature disabled"
)
def test_parl_boundary_postcode_with_address_picker(
    mock_s3_select_postcode_response,
    vi_app_client,
    mock_wdiv,
    sample_postcode_data,
):
    changed_data = sample_postcode_data
    changed_data[1]["new_constituencies_official_identifier"] = "DIFFERENT"
    mock_s3_select_postcode_response.return_value = changed_data

    resp = vi_app_client.get("/api/v1/postcode/AA12AA/")
    assert resp.json()["address_picker"]
    assert resp.json()["parl_boundary_changes"] is None


@pytest.mark.skipif(
    not PARL_BOUNDARY_CHANGES_ENABLED, reason="Parl boundary feature disabled"
)
def test_parl_boundary_postcode_change_type_name(
    mock_s3_select_postcode_response,
    vi_app_client,
    mock_wdiv,
    sample_postcode_data,
):
    changed_data = sample_postcode_data
    changed_data[0]["new_constituencies_name"] = "DIFFERENT"
    changed_data[1]["new_constituencies_name"] = "DIFFERENT"
    mock_s3_select_postcode_response.return_value = changed_data

    resp = vi_app_client.get("/api/v1/postcode/AA12AA/")
    assert resp.json()["parl_boundary_changes"] == {
        "CHANGE_TYPE": "NAME_CHANGE_BOUNDARY_CHANGE",
        "current_constituencies_name": "Harlow",
        "current_constituencies_official_identifier": "gss:E14000729",
        "new_constituencies_name": "DIFFERENT",
        "new_constituencies_official_identifier": "gss:E14001267",
    }


@pytest.mark.skipif(
    not PARL_BOUNDARY_CHANGES_ENABLED, reason="Parl boundary feature disabled"
)
def test_parl_boundary_postcode_no_change(
    mock_s3_select_postcode_response,
    vi_app_client,
    mock_wdiv,
    sample_postcode_data,
):
    changed_data = sample_postcode_data
    for data in changed_data:
        data["new_constituencies_name"] = data["current_constituencies_name"]
        data["new_constituencies_official_identifier"] = data[
            "current_constituencies_official_identifier"
        ]
    mock_s3_select_postcode_response.return_value = changed_data

    resp = vi_app_client.get("/api/v1/postcode/AA12AA/")
    assert resp.json()["parl_boundary_changes"] == {
        "CHANGE_TYPE": "NO_CHANGE",
        "current_constituencies_name": "Harlow",
        "current_constituencies_official_identifier": "gss:E14000729",
        "new_constituencies_name": "Harlow",
        "new_constituencies_official_identifier": "gss:E14000729",
    }
