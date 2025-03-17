import logging
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
            "uprn": "10003707532",
            "address": "HARLOW STUDY CENTRE, WATERHOUSE MOOR, HARLOW",
            "postcode": "AA1 2AA",
            "outcode": "AA1",
            "current_elections": "local.foo.bar.2019-01-01,parl.foo.2019-01-01,parl.foo.2019-12-12",
        },
        {
            "uprn": "100090549541",
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
    caplog,
):
    caplog.set_level(logging.DEBUG)

    sample_data_writer(sample_postcode_data)
    ballots_set = set()
    for row in sample_postcode_data:
        for ballot in row["current_elections"].split(","):
            ballots_set.add(ballot)
    for ballot in ballots_set:
        await mock_ballot_response(ballot, "")

    resp = elections_app_client.get("/api/v1/elections/postcode/AA12AA/")
    assert resp.status_code == 200
    assert resp.json() == {
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
    logging_message = None
    for record in caplog.records:
        if record.message.startswith("dc-postcode-searches"):
            logging_message = record
    assert logging_message


@pytest.mark.asyncio
async def test_postcode_doesnt_exist_in_file(
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

    resp = elections_app_client.get("/api/v1/elections/postcode/AA12AB/")
    assert resp.status_code == 200
    assert resp.json() == {
        "address_picker": False,
        "addresses": [],
        "dates": [],
    }


@pytest.mark.asyncio
async def test_file_not_found(
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

    resp = elections_app_client.get("/api/v1/elections/postcode/notapostcode/")
    assert resp.status_code == 200
    assert resp.json() == {
        "address_picker": False,
        "addresses": [],
        "dates": [],
    }


def test_address_picker(
    elections_app_client,
    sample_data_writer,
    sample_postcode_data,
):
    sample_postcode_data[0]["current_elections"] = "local.other.ward.2019-01-01"
    sample_data_writer(sample_postcode_data)
    resp = elections_app_client.get("/api/v1/elections/postcode/AA12AA/")
    assert resp.status_code == 200
    assert resp.json()["address_picker"] is True
    assert resp.json()["addresses"] == [
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


@pytest.mark.asyncio
async def test_uprn_view(
    elections_app_client,
    sample_data_writer,
    sample_postcode_data,
    mock_ballot_response,
):
    await mock_ballot_response("local.other.ward.2019-01-01", "")
    sample_postcode_data[0]["current_elections"] = "local.other.ward.2019-01-01"
    sample_data_writer(sample_postcode_data)
    resp = elections_app_client.get(
        "/api/v1/elections/postcode/AA12AA/10003707532/"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["address_picker"] is False
    assert len(body["dates"]) == 1


@pytest.mark.asyncio
async def test_uprn_not_found(
    elections_app_client,
    sample_data_writer,
    sample_postcode_data,
    mock_ballot_response,
):
    await mock_ballot_response("local.other.ward.2019-01-01", "")
    sample_postcode_data[0]["current_elections"] = "local.other.ward.2019-01-01"
    sample_data_writer(sample_postcode_data)
    resp = elections_app_client.get("/api/v1/elections/postcode/AA12AA/123/")
    assert resp.status_code == 200
    assert resp.json() == {
        "address_picker": False,
        "addresses": [],
        "dates": [],
    }


@pytest.mark.asyncio
async def test_uprn_duplicate(
    elections_app_client,
    sample_data_writer,
    sample_postcode_data,
    mock_ballot_response,
    caplog,
):
    sample_data_writer(
        [
            {
                "postcode": "AA1 1AA",
                "uprn": "000001",
                "current_elections": ["local.buckinghamshire.abbey.2025-05-01"],
            },
            {
                "postcode": "AA1 1AA",
                "uprn": "000001",
                "current_elections": ["local.buckinghamshire.abbey.2025-05-01"],
            },
        ]
    )

    resp = elections_app_client.get("/api/v1/elections/postcode/AA11AA/000001/")
    assert resp.status_code == 200
    assert resp.json() == {
        "address_picker": False,
        "addresses": [],
        "dates": [],
    }

    message = ""
    for record in caplog.records:
        if record.name == "static_elections_client":
            message = record.msg
    assert message.startswith("UPRN 000001 found 2 times in Parquet file")


@pytest.mark.asyncio
async def test_postcode_no_elections(
    elections_app_client,
    sample_data_writer,
    sample_postcode_data,
    mock_ballot_response,
):
    sample_data_writer(
        [
            {
                "postcode": "AA1 1AA",
                "uprn": "000001",
                "current_elections": [],
            },
            {
                "postcode": "AA1 1AA",
                "uprn": "000002",
                "current_elections": [],
            },
        ]
    )

    resp = elections_app_client.get("/api/v1/elections/postcode/AA11AA/")
    assert resp.status_code == 200
    assert resp.json() == {
        "address_picker": False,
        "addresses": [],
        "dates": [],
    }


@pytest.mark.asyncio
async def test_uprn_no_elections(
    elections_app_client,
    sample_data_writer,
    sample_postcode_data,
    mock_ballot_response,
):
    sample_data_writer(
        [
            {
                "postcode": "AA1 1AA",
                "uprn": "000001",
                "current_elections": [],
            },
            {
                "postcode": "AA1 1AA",
                "uprn": "000002",
                "current_elections": [],
            },
        ]
    )

    resp = elections_app_client.get("/api/v1/elections/postcode/AA11AA/000001/")
    assert resp.status_code == 200
    assert resp.json() == {
        "address_picker": False,
        "addresses": [],
        "dates": [],
    }
