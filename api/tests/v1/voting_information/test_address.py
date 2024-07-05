import httpx
import pytest
from tests.helpers import (
    fixture_map,
    load_fixture,
    load_sandbox_output,
)
from voting_information.elections_api_client import (
    wcivf_ballot_cache_url_from_ballot,
)


def test_no_stitcher_error_with_mismatched_ballots(respx_mock, vi_app_client):
    """
    Dispite the ballots mismatching, don't raise an error

    """

    fixture = load_fixture(
        "addresspc_endpoints/test_multiple_elections", "wdiv"
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

    response = vi_app_client.get("/api/v1/address/1-foo-street-bar-town/")
    assert response.status_code == 200


@pytest.mark.parametrize("postcode", ["AA12AA", "AA12AB", "AA14AA"])
def test_valid(postcode, vi_app_client, respx_mock, api_settings):
    # iterate through the subset of applicable expected inputs/outputs
    # we test against in test_stitcher.py
    fixture = load_fixture(fixture_map[postcode], "wdiv")
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
    response = vi_app_client.get(
        "/api/v1/address/1-foo-street-bar-town/",
    )
    assert expected == response.json()
    assert response.status_code == 200
