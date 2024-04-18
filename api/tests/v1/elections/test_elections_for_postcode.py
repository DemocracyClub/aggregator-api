import tempfile
from pathlib import Path

import polars
import pytest
from endpoints.v1.elections import app
from starlette.testclient import TestClient


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


def test_postcode_returns_ballots(
    elections_app_client, sample_data_writer, sample_postcode_data
):
    sample_data_writer(sample_postcode_data)
    req = elections_app_client.get("/api/v1/elections/postcode/AA12AA/")
    assert req.status_code == 200
    assert req.json() == {
        "address_picker": False,
        "addresses": [],
        "dates": [
            {
                "date": "2019-01-01",
                "ballots": ["local.foo.bar.2019-01-01", "parl.foo.2019-01-01"],
            },
            {
                "date": "2019-12-12",
                "ballots": ["parl.foo.2019-12-12"],
            },
        ],
    }
