from functools import partial
from unittest.mock import Mock, patch
from django.test import TestCase
from api.v1.tests.helpers import load_fixture, mock_proxy_single_request


class ElectionViewTests(TestCase):
    maxDiff = None

    @patch(
        "api.v1.api_client.proxy_single_request",
        partial(
            mock_proxy_single_request, "elections_endpoint/test_every_election_list"
        ),
    )
    def test_list_valid(self):
        response = self.client.get(
            f"/api/v1/elections/", HTTP_AUTHORIZATION="Token foo"
        )
        expected = load_fixture(
            "elections_endpoint/test_every_election_list", "expected_output"
        )
        self.assertDictEqual(expected, response.json())

    def test_list_mock(self):
        mock = Mock(return_value={})
        with patch("api.v1.api_client.EEApiClient.get_election_list", mock):
            self.client.get(
                f"/api/v1/elections/?limit=100&foo=bar", HTTP_AUTHORIZATION="Token foo"
            )
            # this one should pass the GET params down the call stack
            self.assertDictEqual(
                {"limit": "100", "foo": "bar"}, (dict(mock.call_args[0][0].items()))
            )

    @patch(
        "api.v1.api_client.proxy_single_request",
        partial(
            mock_proxy_single_request, "elections_endpoint/test_every_election_single"
        ),
    )
    def test_single_valid(self):
        response = self.client.get(
            f"/api/v1/elections/local.cardiff.ely.by.2019-02-21/",
            HTTP_AUTHORIZATION="Token foo",
        )
        expected = load_fixture(
            "elections_endpoint/test_every_election_single", "expected_output"
        )
        self.assertDictEqual(expected, response.json())

    def test_single_mock(self):
        mock = Mock(return_value={})
        with patch("api.v1.api_client.EEApiClient.get_single_election", mock):
            self.client.get(
                f"/api/v1/elections/local.cardiff.ely.by.2019-02-21/?&foo=bar",
                HTTP_AUTHORIZATION="Token foo",
            )
            mock.assert_called_with("local.cardiff.ely.by.2019-02-21")
