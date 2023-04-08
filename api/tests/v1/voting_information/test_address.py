import httpx
from tests.helpers import (
    fixture_map,
    load_fixture,
    load_sandbox_output,
)


def test_no_stitcher_error_with_mismatched_ballots(respx_mock, vi_app_client):
    """
    Dispite the ballots mismatching, don't raise an error

    """
    respx_mock.get(
        "https://whocanivotefor.co.uk/api/candidates_for_ballots/?utm_medium=devs.DC+API&ballot_ids=mayor.lewisham.2018-05-03%2Clocal.lewisham.blackheath.2018-05-03%2Clocal.lewisham.blackheath.2018-05-10%2Cparl.lewisham-east.by.2018-06-14"
    ).mock(
        return_value=httpx.Response(
            200,
            json=load_fixture(
                "addresspc_endpoints/test_multiple_elections", "wcivf"
            ),
        )
    )

    respx_mock.get(
        "http://wheredoivote.co.uk/api/beta/address/1-foo-street-bar-town/?all_future_ballots=1&utm_medium=devs.DC+API"
    ).mock(
        return_value=httpx.Response(
            200,
            json=load_fixture(
                "addresspc_endpoints/test_multiple_elections", "wdiv"
            ),
        )
    )

    response = vi_app_client.get("/api/v1/address/1-foo-street-bar-town/")
    assert response.status_code == 200


def test_valid(vi_app_client, respx_mock):
    # iterate through the subset of applicable expected inputs/outputs
    # we test against in test_stitcher.py
    for postcode in ["AA12AA", "AA12AB", "AA14AA"]:
        respx_mock.get(
            "http://wheredoivote.co.uk/api/beta/address/1-foo-street-bar-town/?all_future_ballots=1&utm_medium=devs.DC+API"
        ).mock(
            return_value=httpx.Response(
                200, json=load_fixture(fixture_map[postcode], "wdiv")
            )
        )
        respx_mock.get(
            "https://whocanivotefor.co.uk/api/candidates_for_ballots/?utm_medium=devs.DC+API&ballot_ids=mayor.lewisham.2018-05-03%2Clocal.lewisham.blackheath.2018-05-03,local.lewisham.blackheath.2018-05-10,parl.lewisham-east.by.2018-06-14"
        ).mock(
            return_value=httpx.Response(
                200, json=load_fixture(fixture_map[postcode], "wcivf")
            )
        )
        respx_mock.get(
            "https://whocanivotefor.co.uk/api/candidates_for_ballots/?utm_medium=devs.DC+API&ballot_ids=local.westminster.lancaster-gate.by.2018-11-22"
        ).mock(
            return_value=httpx.Response(
                200, json=load_fixture(fixture_map[postcode], "wcivf")
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
