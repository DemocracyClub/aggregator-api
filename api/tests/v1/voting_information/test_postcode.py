import logging
from unittest.mock import Mock

import httpx
import pytest

from tests.helpers import (
    fixture_map,
    load_fixture,
    load_sandbox_output,
)


@pytest.mark.parametrize(
    "postcode,input_fixture", [(k, v) for k, v in fixture_map.items()]
)
def test_valid(vi_app_client, respx_mock, postcode, input_fixture):
    # iterate through the same set of expected inputs/outputs
    # we test against in test_stitcher.py
    respx_mock.get(
        f"http://whocanivotefor.co.uk/api/candidates_for_postcode/?postcode={postcode}"
    ).mock(
        return_value=httpx.Response(
            200,
            json=load_fixture(input_fixture, "wcivf"),
        )
    )

    respx_mock.get(f"http://wheredoivote.co.uk/api/beta/postcode/{postcode}/").mock(
        return_value=httpx.Response(
            200,
            json=load_fixture(input_fixture, "wdiv"),
        )
    )

    expected = load_sandbox_output(postcode, base_url="http://testserver/api/v1/")
    response = vi_app_client.get(f"/api/v1/postcode/{postcode}/")
    assert response.status_code == 200
    assert response.json() == expected


def test_wcivf_missing_ballot(respx_mock, vi_app_client):
    wcivf_data = load_fixture("addresspc_endpoints/test_multiple_elections", "wcivf")
    # del wcivf_data[0]

    respx_mock.get("http://wheredoivote.co.uk/api/beta/postcode/SW1A1AA/").mock(
        return_value=httpx.Response(
            200,
            json=load_fixture("addresspc_endpoints/test_multiple_elections", "wdiv"),
        )
    )
    respx_mock.get(
        "http://whocanivotefor.co.uk/api/candidates_for_postcode/?postcode=SW1A1AA"
    ).mock(
        return_value=httpx.Response(
            200,
            json=load_fixture("addresspc_endpoints/test_multiple_elections", "wcivf"),
        )
    )
    resp = vi_app_client.get(
        "/api/v1/postcode/SW1A1AA/?foo=bar",
    )
    assert resp.status_code == 200
    assert "mayor.lewisham.2018-05-03" in resp.text


def test_logging_working(respx_mock, vi_app_client, caplog):
    caplog.set_level(logging.DEBUG)

    respx_mock.get(
        "http://whocanivotefor.co.uk/api/candidates_for_postcode/?postcode=SW1A1AA"
    ).mock(
        return_value=httpx.Response(
            200,
            json=load_fixture("addresspc_endpoints/test_multiple_elections", "wcivf"),
        )
    )
    respx_mock.get(
        "http://wheredoivote.co.uk/api/beta/postcode/SW1A1AA/"
    ).mock(
        return_value=httpx.Response(
            200,
            json=load_fixture("addresspc_endpoints/test_multiple_elections", "wdiv"),
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
