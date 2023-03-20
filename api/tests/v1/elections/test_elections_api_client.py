import httpx
import pytest
from endpoints.v1.elections import app
from endpoints.v1.elections.voting_information_api_client import EEApiClient
from httpx import QueryParams
from starlette.testclient import TestClient
from tests.helpers import load_fixture


@pytest.fixture(scope="function")
def elections_app_client() -> TestClient:
    return TestClient(app=app.app)


def test_clean_query_params(elections_app_client):
    valid_params = {
        "limit": "50",
        "offset": "200",
        "current": "1",
        "future": "1",
        "coords": "52.290719,-1.935395",
        "metadata": "0",
    }
    invalid_params = {
        "postcode": "SW1A1AA",
        "auth_token": "f00b4r",
        "foo": "bar",
        "utm_medium": "devs.DC API",
        "deleted": "1",
    }
    q = QueryParams()
    q = q.merge(valid_params)
    q = q.merge(invalid_params)

    client = EEApiClient()
    cleaned = client.clean_query_params(q)
    cleaned = dict(cleaned.items())

    for key in valid_params:
        assert key in cleaned
    for key in invalid_params:
        assert key not in cleaned


@pytest.mark.asyncio
async def test_get_election_list(respx_mock, elections_app_client):
    respx_mock.get(
        "https://elections.democracyclub.org.uk/api/elections/"
    ).mock(
        return_value=httpx.Response(
            200,
            json=load_fixture(
                "elections_endpoint/test_every_election_list", "ee"
            ),
        )
    )
    response = elections_app_client.get("/api/v1/elections/")
    expected = load_fixture(
        "elections_endpoint/test_every_election_list", "expected_output"
    )
    assert expected == response.json()


def test_get_single_election(respx_mock, elections_app_client):
    respx_mock.get(
        "https://elections.democracyclub.org.uk/api/elections/local.cardiff.ely.by.2019-02-21/"
    ).mock(
        return_value=httpx.Response(
            200,
            json=load_fixture(
                "elections_endpoint/test_every_election_single", "ee"
            ),
        )
    )

    response = elections_app_client.get(
        "/api/v1/elections/local.cardiff.ely.by.2019-02-21/"
    )
    expected = load_fixture(
        "elections_endpoint/test_every_election_single", "expected_output"
    )
    assert expected == response.json()


def test_filter_single_election_empty():
    client = EEApiClient()
    # if none of the keys we're trying to remove are present
    # we should just pass the object without throwing an exception
    assert {} == client.filter_single_election({})


def test_filter_single_election_valid():
    client = EEApiClient()
    result = client.filter_single_election(
        load_fixture("elections_endpoint/test_every_election_single", "ee")
    )
    expected = load_fixture(
        "elections_endpoint/test_every_election_single", "expected_output"
    )
    assert expected == result


def test_filter_election_list(elections_app_client):
    client = EEApiClient(base_url="http://testserver/")
    input_ = {
        "count": 200,
        "next": "https://elections.democracyclub.org.uk/api/elections/?limit=2&offset=6&foo=bar",
        "previous": "https://elections.democracyclub.org.uk/api/elections/?limit=2&offset=2&foo=bar",
        "results": [
            {
                "election_id": "local.adur.2018-05-03",
                "organisation": {
                    "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/ADU/1974-04-01/",
                    "official_identifier": "ADU",
                },
            },
            {
                "election_id": "local.amber-valley.2018-05-03",
                "organisation": {
                    "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/AMB/1974-04-01/",
                    "official_identifier": "AMB",
                },
            },
        ],
    }
    expected = {
        "count": 200,
        "next": "http://testserver/api/v1/elections/?limit=2&offset=6",
        "previous": "http://testserver/api/v1/elections/?limit=2&offset=2",
        "results": [
            {
                "election_id": "local.adur.2018-05-03",
                "organisation": {"official_identifier": "ADU"},
            },
            {
                "election_id": "local.amber-valley.2018-05-03",
                "organisation": {"official_identifier": "AMB"},
            },
        ],
    }
    assert expected == client.filter_election_list(input_)
