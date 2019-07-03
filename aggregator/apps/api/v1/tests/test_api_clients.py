from functools import partial
from unittest.mock import patch
from django.http import QueryDict
from django.test import TestCase
from django.test.client import RequestFactory
from api.v1.api_client import EEApiClient
from api.v1.tests.helpers import load_fixture, mock_proxy_single_request


class EEApiClientTests(TestCase):
    maxDiff = None

    def setUp(self):
        rf = RequestFactory()
        self.request = rf.get("/foo")

    def test_clean_query_params(self):
        valid_params = {
            "limit": "50",
            "offset": "200",
            "current": "1",
            "future": "1",
            "coords": "52.290719,-1.935395",
            "metadata": "0",
        }
        invalid_params = {
            "postcode": "SW1A1AA",
            "auth_token": "f00b4r",
            "foo": "bar",
            "utm_medium": "devs.DC API",
            "deleted": "1",
        }
        q = QueryDict("", mutable=True)
        q.update(valid_params)
        q.update(invalid_params)

        client = EEApiClient(self.request)
        cleaned = client.clean_query_params(q)
        cleaned = dict(cleaned.items())

        for key in valid_params:
            self.assertTrue(key in cleaned)
        for key in invalid_params:
            self.assertFalse(key in cleaned)

    @patch(
        "api.v1.api_client.proxy_single_request",
        partial(
            mock_proxy_single_request, "elections_endpoint/test_every_election_list"
        ),
    )
    def test_get_election_list(self):
        client = EEApiClient(self.request)
        response = client.get_election_list(QueryDict(""))
        expected = load_fixture(
            "elections_endpoint/test_every_election_list", "expected_output"
        )
        self.assertDictEqual(expected, response)

    @patch(
        "api.v1.api_client.proxy_single_request",
        partial(
            mock_proxy_single_request, "elections_endpoint/test_every_election_single"
        ),
    )
    def test_get_single_election(self):
        client = EEApiClient(self.request)
        response = client.get_single_election("local.cardiff.ely.by.2019-02-21")
        expected = load_fixture(
            "elections_endpoint/test_every_election_single", "expected_output"
        )
        self.assertDictEqual(expected, response)

    def test_filter_single_election_empty(self):
        client = EEApiClient(self.request)
        # if none of the keys we're trying to remove are present
        # we should just pass the object without throwing an exception
        self.assertDictEqual({}, client.filter_single_election({}))

    def test_filter_single_election_valid(self):
        client = EEApiClient(self.request)
        result = client.filter_single_election(
            load_fixture("elections_endpoint/test_every_election_single", "ee")
        )
        expected = load_fixture(
            "elections_endpoint/test_every_election_single", "expected_output"
        )
        self.assertDictEqual(expected, result)

    def test_filter_election_list(self):
        client = EEApiClient(self.request)
        input_ = {
            "count": 200,
            "next": "https://elections.democracyclub.org.uk/api/elections/?limit=2&offset=6&foo=bar",
            "previous": "https://elections.democracyclub.org.uk/api/elections/?limit=2&offset=2&foo=bar",
            "results": [
                {
                    "election_id": "local.adur.2018-05-03",
                    "organisation": {
                        "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/ADU/1974-04-01/",
                        "official_identifier": "ADU",
                    },
                },
                {
                    "election_id": "local.amber-valley.2018-05-03",
                    "organisation": {
                        "url": "https://elections.democracyclub.org.uk/api/organisations/local-authority/AMB/1974-04-01/",
                        "official_identifier": "AMB",
                    },
                },
            ],
        }
        expected = {
            "count": 200,
            "next": "http://testserver/api/v1/elections/?limit=2&offset=6",
            "previous": "http://testserver/api/v1/elections/?limit=2&offset=2",
            "results": [
                {
                    "election_id": "local.adur.2018-05-03",
                    "organisation": {"official_identifier": "ADU"},
                },
                {
                    "election_id": "local.amber-valley.2018-05-03",
                    "organisation": {"official_identifier": "AMB"},
                },
            ],
        }
        self.assertDictEqual(expected, client.filter_election_list(input_))
