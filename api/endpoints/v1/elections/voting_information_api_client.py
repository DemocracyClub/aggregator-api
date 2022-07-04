from urllib.parse import urlparse, parse_qs

from httpx import QueryParams

from common.url_resolver import build_absolute_url
from common import settings
from common.api_client import BaseAPIClient
from common.async_requests import AsyncRequester


class EEApiClient(BaseAPIClient):
    def clean_query_params(self, params):
        """
        Take a django QueryDict object and return another QueryDict
        containing only the specified keys.

        We should use this both:
        - before passing a query string from devs.DC to EE and
        - before passing a URL with a query string from EE
          back to the devs.DC user.

        There are several things this achieves:
        1. There are some params that the devs.DC API accepts
           that we don't want to pass through to the EE API (e.g: auth_token)
        2. There are some params supported by the EE API
           that we don't want to expose to dev.DC users (e.g: postcode)
        3. In future, if we wanted to pass additional params to EE
           (e.g: a tracking param or API key, like we do with WDIV),
           they'll come back reflected in the next/previous URLs.
           Cleaning prevents us exposing those params to the devs.DC user.
        """
        allowed_query_params = [
            "limit",
            "offset",
            "current",
            "future",
            "coords",
            "metadata",
            "identifier_type",
        ]
        q = QueryParams({k: v for k, v in params.items() if k in allowed_query_params})
        return q

    async def get_single_election(self, slug):
        ee_url = f"{settings.EE_BASE_URL}elections/{slug}/"
        request_urls = {"ee": {"url": ee_url}}
        requester = AsyncRequester(request_dict=request_urls)
        responses = await requester.get_urls()
        return self.filter_single_election(responses["ee"]["response"].json())

    async def get_election_list(self, query_dict=None):
        if not query_dict:
            query_dict = QueryParams()
        ee_url = f"{settings.EE_BASE_URL}elections/"
        request_urls = {"ee": {"url": ee_url, "params": query_dict}}
        requester = AsyncRequester(request_dict=request_urls)
        responses = await requester.get_urls()
        return self.filter_election_list(responses["ee"]["response"].json())

    def filter_single_election(self, election):
        election.pop("deleted", None)
        election.pop("explanation", None)
        election.pop("tmp_election_id", None)
        election.pop("group_type", None)

        if "organisation" in election and election["organisation"]:
            election["organisation"].pop("url", None)

        if "division" in election and election["division"]:
            election["division"].pop("division_subtype", None)
            election["division"].pop("geography_curie", None)
            election["division"].pop("mapit_generation_low", None)
            election["division"].pop("mapit_generation_high", None)
            election["division"]["divisionset"].pop("mapit_generation_id", None)

        return election

    def filter_election_list(self, response):
        # links in header
        for key in ["next", "previous"]:
            if response[key]:
                parsed_url = urlparse(response[key])
                q = parse_qs(parsed_url.query)
                q = self.clean_query_params(q)
                base = build_absolute_url(self.base_url, "election_list")
                response[key] = f"{base}?{q}"

        # list of election objects
        response["results"] = [
            self.filter_single_election(election) for election in response["results"]
        ]

        return response
