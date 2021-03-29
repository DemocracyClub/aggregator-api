from functools import partial
from unittest.mock import Mock, patch
from django.test import TestCase
from api.v1.stitcher import StitcherValidationError
from api.v1.tests.helpers import (
    fixture_map,
    load_fixture,
    load_sandbox_output,
    mock_proxy_single_request,
)


class AddressViewTests(TestCase):
    maxDiff = None

    @patch(
        "api.v1.api_client.proxy_single_request",
        partial(
            mock_proxy_single_request, "addresspc_endpoints/test_multiple_elections"
        ),
    )
    def test_no_stitcher_error_with_mismatched_ballots(self):
        """
        Dispite the ballots mismatching, don't raise an error

        """
        response = self.client.get(
            "/api/v1/address/1-foo-street-bar-town/", HTTP_AUTHORIZATION="Token foo"
        )
        self.assertEqual(200, response.status_code)

    def test_valid(self):
        # iterate through the subset of applicable expected inputs/outputs
        # we test against in test_stitcher.py
        for postcode in ["AA12AA", "AA12AB", "AA14AA"]:
            mock = partial(mock_proxy_single_request, fixture_map[postcode])
            expected = load_sandbox_output(
                postcode, base_url="http://testserver/api/v1/"
            )
            with patch("api.v1.api_client.proxy_single_request", mock):
                response = self.client.get(
                    "/api/v1/address/1-foo-street-bar-town/",
                    HTTP_AUTHORIZATION="Token foo",
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
        with patch("api.v1.api_client.WdivWcivfApiClient.get_data_for_address", mock):
            self.client.get(
                "/api/v1/address/1-foo-street-bar-town/?foo=bar",
                HTTP_AUTHORIZATION="Token foo",
            )
            mock.assert_called_with("1-foo-street-bar-town")
