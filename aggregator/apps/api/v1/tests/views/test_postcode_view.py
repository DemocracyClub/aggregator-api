import logging
from functools import partial
from unittest.mock import Mock, patch

from api.v1.tests.helpers import (
    fixture_map,
    load_fixture,
    load_sandbox_output,
    mock_proxy_multiple_requests,
)
from django.test import TestCase


class PostcodeViewTests(TestCase):
    maxDiff = None

    def test_valid(self):
        # iterate through the same set of expected inputs/outputs
        # we test against in test_stitcher.py
        for postcode, input_fixture in fixture_map.items():
            with self.subTest(postcode=postcode, input_fixture=input_fixture):
                mock = partial(mock_proxy_multiple_requests, input_fixture)
                expected = load_sandbox_output(
                    postcode, base_url="http://testserver/api/v1/"
                )
                with patch("api.v1.api_client.proxy_multiple_requests", mock):
                    response = self.client.get(
                        f"/api/v1/postcode/{postcode}/", HTTP_AUTHORIZATION="Token foo"
                    )
                    self.assertDictEqual(expected, response.json())
                    self.assertEqual(200, response.status_code)

    def test_mock(self):
        mock = Mock(
            return_value=(
                load_fixture("addresspc_endpoints/test_multiple_elections", "wdiv"),
                load_fixture("addresspc_endpoints/test_multiple_elections", "wcivf"),
            )
        )
        with patch("api.v1.api_client.WdivWcivfApiClient.get_data_for_postcode", mock):
            self.client.get(
                "/api/v1/postcode/SW1A1AA/?foo=bar", HTTP_AUTHORIZATION="Token foo"
            )
            mock.assert_called_with("SW1A1AA")

    def test_wcivf_missing_ballot(self):
        wcivf_data = load_fixture(
            "addresspc_endpoints/test_multiple_elections", "wcivf"
        )
        del wcivf_data[0]
        mock = Mock(
            return_value=(
                load_fixture("addresspc_endpoints/test_multiple_elections", "wdiv"),
                wcivf_data,
            )
        )
        with patch("api.v1.api_client.WdivWcivfApiClient.get_data_for_postcode", mock):
            resp = self.client.get(
                "/api/v1/postcode/SW1A1AA/?foo=bar", HTTP_AUTHORIZATION="Token foo"
            )
            self.assertEqual(resp.status_code, 200)
            self.assertNotContains(resp, "mayor.lewisham.2018-05-03")


def test_logging_working(client, caplog):
    caplog.set_level(logging.DEBUG)

    wcivf_data = load_fixture("addresspc_endpoints/test_multiple_elections", "wcivf")
    del wcivf_data[0]
    mock = Mock(
        return_value=(
            load_fixture("addresspc_endpoints/test_multiple_elections", "wdiv"),
            wcivf_data,
        )
    )
    with patch("api.v1.api_client.WdivWcivfApiClient.get_data_for_postcode", mock):
        client.get("/api/v1/postcode/SW1A1AA/?foo=bar", HTTP_AUTHORIZATION="Token foo")

    logging_message = None
    for record in caplog.records:
        if record.message.startswith("dc-postcode-searches"):
            logging_message = record
    assert logging_message
    assert '"postcode": "SW1A1AA"' in logging_message.message
    assert '"dc_product": "AGGREGATOR_API"' in logging_message.message
    assert '"api_key": "foo"' in logging_message.message
