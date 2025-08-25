import logging

import httpx
import pytest
from voting_information.elections_api_client import (
    wcivf_ballot_cache_url_from_ballot,
)

from tests.helpers import (
    fixture_map,
    load_fixture,
    load_sandbox_output,
)


@pytest.mark.parametrize("postcode,input_fixture", list(fixture_map.items()))
def test_valid(
    vi_app_client, respx_mock, postcode, input_fixture, api_settings
):
    # iterate through the same set of expected inputs/outputs
    # we test against in test_stitcher.py

    fixture = load_fixture(input_fixture, "wdiv")
    respx_mock.get(
        f"https://wheredoivote.co.uk/api/beta/postcode/{postcode}/"
    ).mock(
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

    expected = load_sandbox_output(
        postcode, base_url="http://testserver/api/v1/"
    )
    response = vi_app_client.get(f"/api/v1/postcode/{postcode}/")
    assert response.status_code == 200
    assert response.json() == expected


def test_wcivf_missing_ballot(respx_mock, vi_app_client, api_settings):
    load_fixture("addresspc_endpoints/test_multiple_elections", "wcivf")
    fixture = load_fixture(
        "addresspc_endpoints/test_multiple_elections", "wdiv"
    )
    respx_mock.get(
        "https://wheredoivote.co.uk/api/beta/postcode/SW1A1AA/"
    ).mock(
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
                json=load_fixture(
                    "addresspc_endpoints/test_multiple_elections",
                    ballot["ballot_paper_id"],
                ),
            )
        )
    resp = vi_app_client.get(
        "/api/v1/postcode/SW1A1AA/?foo=bar",
    )
    assert resp.status_code == 200
    assert "mayor.lewisham.2018-05-03" in resp.text


def test_logging_working(respx_mock, vi_app_client, caplog, api_settings):
    caplog.set_level(logging.DEBUG)
    fixture = load_fixture(
        "addresspc_endpoints/test_multiple_elections", "wdiv"
    )
    respx_mock.get(
        "https://wheredoivote.co.uk/api/beta/postcode/SW1A1AA/"
    ).mock(
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
                json=load_fixture(
                    "addresspc_endpoints/test_multiple_elections",
                    ballot["ballot_paper_id"],
                ),
            )
        )

    vi_app_client.get(
        "/api/v1/postcode/SW1A1AA/",
        params={
            "foo": "bar",
            "utm_source": "test",
            "utm_campaign": "better_tracking",
            "utm_medium": "pytest",
        },
    )

    logging_message = None
    for record in caplog.records:
        if record.message.startswith("dc-postcode-searches"):
            logging_message = record
    assert logging_message
    assert '"postcode": "SW1A1AA"' in logging_message.message
    assert '"dc_product": "AGGREGATOR_API"' in logging_message.message
    assert '"api_key": "local-dev"' in logging_message.message
    assert '"utm_source": "test"' in logging_message.message
    assert '"utm_campaign": "better_tracking"' in logging_message.message
    assert '"utm_medium": "pytest"' in logging_message.message
