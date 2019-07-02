from functools import partial
from unittest.mock import Mock, patch
from django.test import TestCase
from api.v1.stitcher import StitcherValidationError
from api.v1.tests.helpers import (
    fixture_map,
    load_fixture,
    load_sandbox_output,
    mock_proxy_multiple_requests,
)


def stitcher_error(*args, **kwargs):
    raise StitcherValidationError("foo")


class PostcodeViewTests(TestCase):
    maxDiff = None

    @patch(
        "api.v1.api_client.proxy_multiple_requests",
        partial(mock_proxy_multiple_requests, "addresspc_endpoints/test_no_elections"),
    )
    @patch("api.v1.stitcher.Stitcher.validate", stitcher_error)
    def test_stitcher_error(self):
        # we're mocking a valid set of WDIV/WCIVF responses here
        # but when we try to parse them, Stitcher will throw an error
        response = self.client.get(
            f"/api/v1/postcode/SW1A1AA/", HTTP_AUTHORIZATION="Token foo"
        )
        self.assertEqual(500, response.status_code)
        self.assertDictEqual({"message": "Internal Server Error"}, response.json())

    def test_valid(self):
        # iterate through the same set of expected inputs/outputs
        # we test against in test_stitcher.py
        for postcode, input_fixture in fixture_map.items():
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
                f"/api/v1/postcode/SW1A1AA/?foo=bar", HTTP_AUTHORIZATION="Token foo"
            )
            mock.assert_called_with("SW1A1AA")
