import json

import httpx
from common.auth_models import User
from elections_api_client import wcivf_ballot_cache_url_from_ballot
from tests.helpers import load_fixture, load_sandbox_output
from voting_information.app import handler as voting_information_handler


def test_unauthenticated():
    user = User.unauthenticated_user()
    assert user.user_id == "unauthenticated_user"


def test_authentication_via_aws_like_scope(
    mangum_app_client, respx_mock, api_settings
):
    """
    Use Mangum to force the AWS-like scope, so we can test that the
    authentication middleware is working properly
    """
    api_settings.PARL_BOUNDARY_CHANGES_ENABLED = False
    postcode = "AA11AA"
    fixture = load_fixture("addresspc_endpoints/test_no_elections", "wdiv")
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
                json=load_fixture(
                    "addresspc_endpoints/test_no_elections",
                    ballot["ballot_paper_id"],
                ),
            )
        )

    expected = load_sandbox_output(
        postcode, base_url="http://testserver/api/v1/"
    )

    response = mangum_app_client(
        voting_information_handler, f"/api/v1/postcode/{postcode}/"
    )
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == expected
