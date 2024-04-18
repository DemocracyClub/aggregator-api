import tempfile
from pathlib import Path

import httpx
import polars
import pytest
from endpoints.v1.elections import app
from starlette.testclient import TestClient
from static_elections_client import ballot_paper_id_to_static_url


@pytest.fixture(scope="function")
def elections_app_client() -> TestClient:
    return TestClient(app=app.app)


@pytest.fixture()
def temp_data_root(api_settings):
    with tempfile.TemporaryDirectory("data") as tmp:
        api_settings.ELECTIONS_DATA_PATH = tmp
        yield tmp


@pytest.fixture()
def sample_postcode_data():
    return [
        {
            "uprn": 10003707532,
            "address": "HARLOW STUDY CENTRE, WATERHOUSE MOOR, HARLOW",
            "postcode": "AA1 2AA",
            "outcode": "AA1",
            "current_elections": "local.foo.bar.2019-01-01,parl.foo.2019-01-01,parl.foo.2019-12-12",
        },
        {
            "uprn": 100090549541,
            "address": "208 WATERHOUSE MOOR, HARLOW",
            "postcode": "AA1 2AA",
            "outcode": "AA1",
            "current_elections": "local.foo.bar.2019-01-01,parl.foo.2019-01-01,parl.foo.2019-12-12",
        },
    ]


@pytest.fixture
def sample_data_writer(temp_data_root):
    def write_data(data):
        df = polars.DataFrame(data)
        df_root = Path(temp_data_root)
        df_root.mkdir(exist_ok=True, parents=True)
        df_path = df_root / "AA1.parquet"
        df.write_parquet(df_path)

    yield write_data


@pytest.fixture
def mock_ballot_response(respx_mock):
    async def ballot_route(ballot_paper_id, return_value, status_code=200):
        url = ballot_paper_id_to_static_url(ballot_paper_id)
        return respx_mock.get(url).mock(
            return_value=httpx.Response(
                200,
                json={
                    "ballot_paper_id": ballot_paper_id,
                    "poll_open_date": ballot_paper_id.rsplit(".", 1)[-1],
                },
            )
        )

    return ballot_route


@pytest.mark.asyncio
async def test_postcode_returns_ballots(
    elections_app_client,
    sample_data_writer,
    sample_postcode_data,
    mock_ballot_response,
):
    sample_data_writer(sample_postcode_data)
    ballots_set = set()
    for row in sample_postcode_data:
        for ballot in row["current_elections"].split(","):
            ballots_set.add(ballot)
    for ballot in ballots_set:
        await mock_ballot_response(ballot, "")

    req = elections_app_client.get("/api/v1/elections/postcode/AA12AA/")
    assert req.status_code == 200
    assert req.json() == {
        "address_picker": False,
        "addresses": [],
        "dates": [
            {
                "date": "2019-01-01",
                "ballots": [
                    {
                        "ballot_paper_id": "local.foo.bar.2019-01-01",
                        "poll_open_date": "2019-01-01",
                    },
                    {
                        "ballot_paper_id": "parl.foo.2019-01-01",
                        "poll_open_date": "2019-01-01",
                    },
                ],
            },
            {
                "date": "2019-12-12",
                "ballots": [
                    {
                        "ballot_paper_id": "parl.foo.2019-12-12",
                        "poll_open_date": "2019-12-12",
                    }
                ],
            },
        ],
    }


def test_address_picker(
    elections_app_client,
    sample_data_writer,
    sample_postcode_data,
):
    sample_postcode_data[0]["current_elections"] = "local.other.ward.2019-01-01"
    sample_data_writer(sample_postcode_data)
    req = elections_app_client.get("/api/v1/elections/postcode/AA12AA/")
    assert req.status_code == 200
    assert req.json()["address_picker"] is True
    assert req.json()["addresses"] == [
        {
            "address": "HARLOW STUDY CENTRE, WATERHOUSE MOOR, HARLOW",
            "postcode": "AA1 2AA",
            "slug": "10003707532",
            "url": "http://testserver/api/v1/elections/postcode/AA12AA/10003707532/",
        },
        {
            "address": "208 WATERHOUSE MOOR, HARLOW",
            "postcode": "AA1 2AA",
            "slug": "100090549541",
            "url": "http://testserver/api/v1/elections/postcode/AA12AA/100090549541/",
        },
    ]


def test_uprn_view(
    elections_app_client,
    sample_data_writer,
    sample_postcode_data,
):
    sample_postcode_data[0]["current_elections"] = "local.other.ward.2019-01-01"
    sample_data_writer(sample_postcode_data)
    req = elections_app_client.get(
        "/api/v1/elections/postcode/AA12AA/10003707532/"
    )
    assert req.status_code == 200
    assert req.json()["address_picker"] is False
