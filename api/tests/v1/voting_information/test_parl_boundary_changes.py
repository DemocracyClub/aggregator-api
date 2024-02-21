import os
import tempfile
from pathlib import Path

import boto3
import httpx
import polars
import pytest
from common.conf import settings
from elections_api_client import wcivf_ballot_cache_url_from_ballot
from moto import mock_aws
from tests.helpers import fixture_map, load_fixture

BUCKET_NAME = "addressbase-lookups.development"


@pytest.fixture()
def temp_parl_data_root(api_settings):
    with tempfile.TemporaryDirectory("parl-data") as tmp:
        api_settings.PARL_BOUNDARY_CHANGES_ENABLED = True
        api_settings.LOCAL_DATA_PATH = tmp
        yield tmp


@pytest.fixture()
def sample_postcode_data():
    return [
        {
            "uprn": 10003707532,
            "address": "HARLOW STUDY CENTRE, WATERHOUSE MOOR, HARLOW",
            "postcode": "AA1 2AA",
            "outcode": "AA1",
            "current_constituencies_official_identifier": "gss:E14000729",
            "current_constituencies_name": "Harlow",
            "new_constituencies_official_identifier": "gss:E14001267",
            "new_constituencies_name": "Harlow",
        },
        {
            "uprn": 100090549541,
            "address": "208 WATERHOUSE MOOR, HARLOW",
            "postcode": "AA1 2AA",
            "outcode": "AA1",
            "current_constituencies_official_identifier": "gss:E14000729",
            "current_constituencies_name": "Harlow",
            "new_constituencies_official_identifier": "gss:E14001267",
            "new_constituencies_name": "Harlow",
        },
    ]


@pytest.fixture
def sample_data_writer(temp_parl_data_root):
    def write_data(data):
        df = polars.DataFrame(data)
        df_root = (
            Path(temp_parl_data_root) / settings.PARL_BOUNDARY_DATA_KEY_PREFIX
        )
        df_root.mkdir(exist_ok=True, parents=True)
        df_path = df_root / "AA1.parquet"
        df.write_parquet(df_path)

    yield write_data


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


def test_parl_boundary_postcode_no_s3_data(
    vi_app_client, mock_wdiv, sample_data_writer
):
    resp = vi_app_client.get("/api/v1/postcode/AA12AA/?parl_boundaries=1")
    assert resp.json()["parl_boundary_changes"] is None


def test_parl_boundary_postcode_no_address_picker(
    sample_postcode_data,
    sample_data_writer,
    vi_app_client,
    mock_wdiv,
):
    sample_data_writer(sample_postcode_data)
    resp = vi_app_client.get("/api/v1/postcode/AA12AA/?parl_boundaries=1")
    assert resp.json()["parl_boundary_changes"] == {
        "CHANGE_TYPE": "BOUNDARY_CHANGE",
        "current_constituencies_name": "Harlow",
        "current_constituencies_official_identifier": "gss:E14000729",
        "new_constituencies_name": "Harlow",
        "new_constituencies_official_identifier": "gss:E14001267",
    }


def test_parl_boundary_postcode_with_address_picker(
    sample_postcode_data,
    sample_data_writer,
    vi_app_client,
    mock_wdiv,
):
    changed_data = sample_postcode_data
    changed_data[1]["new_constituencies_official_identifier"] = "DIFFERENT"
    sample_data_writer(changed_data)

    # Make sure we don't get an address picker without the par boundaries
    resp = vi_app_client.get("/api/v1/postcode/AA12AA/").json()
    assert not resp["address_picker"]

    resp = vi_app_client.get(
        "/api/v1/postcode/AA12AA/?parl_boundaries=1"
    ).json()
    assert resp["address_picker"]
    assert resp["parl_boundary_changes"] is None
    assert resp["addresses"] == [
        {
            "address": "HARLOW STUDY CENTRE, WATERHOUSE MOOR, HARLOW",
            "postcode": "AA1 2AA",
            "slug": 10003707532,
            "url": "http://testserver/api/v1/address/10003707532/",
        },
        {
            "address": "208 WATERHOUSE MOOR, HARLOW",
            "postcode": "AA1 2AA",
            "slug": 100090549541,
            "url": "http://testserver/api/v1/address/100090549541/",
        },
    ]


def test_parl_boundary_postcode_change_type_name(
    vi_app_client, mock_wdiv, sample_postcode_data, sample_data_writer
):
    changed_data = sample_postcode_data
    changed_data[0]["new_constituencies_name"] = "DIFFERENT"
    changed_data[1]["new_constituencies_name"] = "DIFFERENT"
    sample_data_writer(changed_data)

    resp = vi_app_client.get("/api/v1/postcode/AA12AA/?parl_boundaries=1")
    assert resp.json()["parl_boundary_changes"] == {
        "CHANGE_TYPE": "NAME_CHANGE_BOUNDARY_CHANGE",
        "current_constituencies_name": "Harlow",
        "current_constituencies_official_identifier": "gss:E14000729",
        "new_constituencies_name": "DIFFERENT",
        "new_constituencies_official_identifier": "gss:E14001267",
    }


def test_parl_boundary_postcode_no_change(
    vi_app_client, mock_wdiv, sample_postcode_data, sample_data_writer
):
    changed_data = sample_postcode_data
    for data in changed_data:
        data["new_constituencies_name"] = data["current_constituencies_name"]
        data["new_constituencies_official_identifier"] = data[
            "current_constituencies_official_identifier"
        ]
    sample_data_writer(changed_data)
    resp = vi_app_client.get("/api/v1/postcode/AA12AA/?parl_boundaries=1")
    assert resp.json()["parl_boundary_changes"] == {
        "CHANGE_TYPE": "NO_CHANGE",
        "current_constituencies_name": "Harlow",
        "current_constituencies_official_identifier": "gss:E14000729",
        "new_constituencies_name": "Harlow",
        "new_constituencies_official_identifier": "gss:E14000729",
    }
