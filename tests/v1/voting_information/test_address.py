import logging
from unittest.mock import patch

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


def test_no_stitcher_error_with_mismatched_ballots(respx_mock, vi_app_client):
    """
    Dispite the ballots mismatching, don't raise an error

    """

    fixture = load_fixture(
        "addresspc_endpoints/test_multiple_elections", "wdiv_address"
    )
    respx_mock.get(
        "https://wheredoivote.co.uk/api/beta/address/1-foo-street-bar-town/?all_future_ballots=1&utm_medium=devs.DC+API"
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
    with patch(
        "api.endpoints.v1.voting_information.address.DCWidePostcodeLoggingClient.log"
    ) as mock_log:
        response = vi_app_client.get("/api/v1/address/1-foo-street-bar-town/")
        mock_log.assert_called_once()
    assert response.status_code == 200


@pytest.mark.parametrize("postcode", ["AA12AA", "AA12AB", "AA14AA"])
def test_valid(postcode, vi_app_client, respx_mock, api_settings):
    # iterate through the subset of applicable expected inputs/outputs
    # we test against in test_stitcher.py
    fixture = load_fixture(fixture_map[postcode], "wdiv_address")
    respx_mock.get(
        "https://wheredoivote.co.uk/api/beta/address/1-foo-street-bar-town/?all_future_ballots=1&utm_medium=devs.DC+API"
    ).mock(return_value=httpx.Response(200, json=fixture))

    for ballot in fixture["ballots"]:
        respx_mock.get(
            wcivf_ballot_cache_url_from_ballot(ballot["ballot_paper_id"])
        ).mock(
            return_value=httpx.Response(
                200,
                json=load_fixture(
                    fixture_map[postcode],
                    ballot["ballot_paper_id"],
                ),
            )
        )

    expected = load_sandbox_output(
        postcode, base_url="http://testserver/api/v1/"
    )

    with patch(
        "api.endpoints.v1.voting_information.address.DCWidePostcodeLoggingClient.log"
    ) as mock_log:
        response = vi_app_client.get(
            "/api/v1/address/1-foo-street-bar-town/",
        )
        mock_log.assert_called_once()

    assert expected == response.json()
    assert response.status_code == 200


@pytest.mark.parametrize(
    "postcode,fixture_name,expected_had_election",
    [
        ("AA1 4AA", "addresspc_endpoints/test_multiple_elections", "true"),
        ("AA1 1AA", "addresspc_endpoints/test_no_elections", "false"),
    ],
)
def test_logging_working(
    respx_mock,
    vi_app_client,
    caplog,
    api_settings,
    postcode,
    fixture_name,
    expected_had_election,
):
    caplog.set_level(logging.DEBUG)
    fixture = load_fixture(fixture_name, "wdiv_address")
    respx_mock.get(
        "https://wheredoivote.co.uk/api/beta/address/1-foo-street-bar-town/?all_future_ballots=1&utm_medium=devs.DC+API"
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
                    fixture_name,
                    ballot["ballot_paper_id"],
                ),
            )
        )

    vi_app_client.get(
        "/api/v1/address/1-foo-street-bar-town/",
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
    assert f'"postcode": "{postcode}"' in logging_message.message
    assert '"dc_product": "AGGREGATOR_API"' in logging_message.message
    assert '"api_key": "local-dev"' in logging_message.message
    assert '"utm_source": "test"' in logging_message.message
    assert '"utm_campaign": "better_tracking"' in logging_message.message
    assert '"utm_medium": "pytest"' in logging_message.message
    assert f'"had_election": {expected_had_election}' in logging_message.message


def test_no_postcode_logs_error(respx_mock, vi_app_client, api_settings):
    """
    When no postcode is found in the response, log error to Sentry but still return the response
    """
    fixture = load_fixture(
        "addresspc_endpoints/test_no_elections", "wdiv_address"
    )
    respx_mock.get(
        "https://wheredoivote.co.uk/api/beta/address/1-foo-street-bar-town/?all_future_ballots=1&utm_medium=devs.DC+API"
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
                    "addresspc_endpoints/test_no_elections",
                    ballot["ballot_paper_id"],
                ),
            )
        )

    with patch(
        "api.endpoints.v1.voting_information.address.sentry_logger.error"
    ) as mock_sentry_error, patch(
        "api.endpoints.v1.voting_information.address.Stitcher.make_result_known_response"
    ) as mock_result:
        # Mock the result to have no postcode
        mock_result.return_value = {
            "dates": [],
            "postcode_location": {"properties": {}},  # No postcode
        }
        response = vi_app_client.get("/api/v1/address/1-foo-street-bar-town/")

        # Verify Sentry error was logged with correct message and attributes
        mock_sentry_error.assert_called_once()
        call_args = mock_sentry_error.call_args
        assert (
            call_args[0][0]
            == "WDIV didn't return a postcode for uprn:1-foo-street-bar-town"
        )
        assert "uprn" in call_args[1]["attributes"]
        assert "api_key" in call_args[1]["attributes"]

    # Verify response is still returned successfully
    assert response.status_code == 200
