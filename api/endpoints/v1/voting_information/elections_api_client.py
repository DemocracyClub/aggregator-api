import contextlib
from json import JSONDecodeError

import httpx
from common import settings
from common.async_requests import AsyncRequester, UpstreamApiError
from common.http_client import app_httpx_client
from httpx import QueryParams

SUPPRESS = [JSONDecodeError, httpx.HTTPError]
if settings.DEBUG:
    SUPPRESS = []


def wcivf_ballot_cache_url_from_ballot(ballot_paper_id):
    parts = ballot_paper_id.split(".")
    path = "/".join((parts[-1], parts[0], parts[1], f"{ballot_paper_id}.json"))
    return f"{settings.WCIVF_BALLOT_CACHE_URL}{path}"


class WdivWcivfApiClient:
    @property
    def wdiv_params(self):
        params = QueryParams(
            all_future_ballots=1, utm_medium=settings.USER_AGENT
        )
        if settings.WDIV_API_KEY:
            params["auth_token"] = settings.WDIV_API_KEY
        return params

    @property
    def wcivf_params(self) -> QueryParams:
        return QueryParams(utm_medium=settings.USER_AGENT)

    async def get_data_for_postcode(self, postcode):
        wdiv_url = f"{settings.WDIV_BASE_URL}postcode/{postcode}/"
        wdiv_result = app_httpx_client.get(wdiv_url, params=self.wdiv_params)
        if wdiv_result.status_code >= 400:
            raise UpstreamApiError(wdiv_result)
        wdiv_result.raise_for_status()

        wdiv_json = wdiv_result.json()

        wcivf_json = []

        if wdiv_json["ballots"]:
            ballot_ids = [b["ballot_paper_id"] for b in wdiv_json["ballots"]]
            for ballot in ballot_ids:
                resp = app_httpx_client.get(
                    wcivf_ballot_cache_url_from_ballot(ballot)
                )
                print(resp.url)
                with contextlib.suppress(*SUPPRESS):
                    wcivf_json.append(resp.json())

        return wdiv_json, wcivf_json

    async def get_data_for_address(self, slug):
        wdiv_url = f"{settings.WDIV_BASE_URL}address/{slug}/"

        request_urls = {"wdiv": {"url": wdiv_url, "params": self.wdiv_params}}

        # Async has no value here as it's a single URL, but it's a consistent
        # interface, so we may as well use it
        requester = AsyncRequester(request_dict=request_urls)
        # This can raise a UpstreamApiError
        responses = await requester.get_urls()
        wdiv_json = responses["wdiv"]["response"].json()

        wcivf_json = []
        if wdiv_json["ballots"]:
            ballot_ids = [b["ballot_paper_id"] for b in wdiv_json["ballots"]]
            for ballot_paper_id in ballot_ids:
                resp = app_httpx_client.get(
                    wcivf_ballot_cache_url_from_ballot(ballot_paper_id)
                )
                print(resp.url)
                with contextlib.suppress(*SUPPRESS):
                    if data := resp.json():
                        wcivf_json.append(data)

        return wdiv_json, wcivf_json
