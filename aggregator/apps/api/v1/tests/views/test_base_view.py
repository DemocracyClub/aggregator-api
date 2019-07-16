import aiohttp
from unittest.mock import patch
from django.test import TestCase
from api.v1.api_client import UpstreamApiError


def aiohttp_error(*args, **kwargs):
    raise aiohttp.ClientConnectorError(connection_key="foo", os_error=OSError())


def api_error(*args, **kwargs):
    raise UpstreamApiError("oh noes!!", 500)


class BaseViewTests(TestCase):
    """
    Tests for the BaseView (abstract) class functionality
    using PostcodeView as a concrete implementation
    """

    maxDiff = None

    def test_no_api_key(self):
        response = self.client.get("/api/v1/postcode/SW1A1AA/")
        self.assertEqual(401, response.status_code)

    @patch("api.v1.views.PostcodeView.get_response", aiohttp_error)
    def test_connection_error(self):
        # we can't contact the upstream API
        response = self.client.get(
            "/api/v1/postcode/SW1A1AA/", HTTP_AUTHORIZATION="Token foo"
        )
        self.assertEqual(500, response.status_code)
        self.assertDictEqual({"message": "Backend Connection Error"}, response.json())

    @patch("api.v1.views.PostcodeView.get_response", api_error)
    def test_api_error(self):
        # if the upstream API responds with an error response
        # we just forward it to the client
        response = self.client.get(
            f"/api/v1/postcode/SW1A1AA/", HTTP_AUTHORIZATION="Token foo"
        )
        self.assertEqual(500, response.status_code)
        self.assertDictEqual({"message": "oh noes!!"}, response.json())
