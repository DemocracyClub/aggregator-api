import contextlib
from json import JSONDecodeError

import httpx
from common.async_requests import UpstreamApiError
from common.conf import settings
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
    def __init__(self, query_params=None):
        if not query_params:
            query_params = {}
        self.query_params = query_params

    @property
    def wdiv_params(self):
        params = QueryParams(
            all_future_ballots=1, utm_medium=settings.USER_AGENT
        )
        if "include_current" in self.query_params:
            params = params.set("include_current", "1")

        if settings.WDIV_API_KEY:
            return params.set("auth_token", settings.WDIV_API_KEY)

        return params

    @property
    def wcivf_params(self) -> QueryParams:
        return QueryParams(utm_medium=settings.USER_AGENT)

    def get_wdiv_json(self, url):
        resp = app_httpx_client.get(url, params=self.wdiv_params)
        if resp.status_code >= 400:
            raise UpstreamApiError(resp)
        resp.raise_for_status()
        return resp.json()

    def get_wcivf_json(self, wdiv_json):
        # This could be async for when there are multiple ballots
        wcivf_json = []
        if wdiv_json["ballots"]:
            ballot_ids = [b["ballot_paper_id"] for b in wdiv_json["ballots"]]
            for ballot in ballot_ids:
                resp = app_httpx_client.get(
                    wcivf_ballot_cache_url_from_ballot(ballot)
                )
                if resp.status_code != 200:
                    # For some reason we're not able to add this ballot,
                    # but don't raise an error about it
                    for i, wdiv_ballot in enumerate(wdiv_json["ballots"]):
                        if wdiv_ballot["ballot_paper_id"] == ballot:
                            del wdiv_json["ballots"][i]
                    continue
                with contextlib.suppress(*SUPPRESS):
                    wcivf_json.append(resp.json())

        return wcivf_json

    def get_data_for_postcode(self, postcode):
        wdiv_url = f"{settings.WDIV_BASE_URL}postcode/{postcode}/"
        wdiv_json = self.get_wdiv_json(wdiv_url)

        wcivf_json = self.get_wcivf_json(wdiv_json)
        return wdiv_json, wcivf_json

    def get_data_for_address(self, slug):
        wdiv_url = f"{settings.WDIV_BASE_URL}address/{slug}/"
        wdiv_json = self.get_wdiv_json(wdiv_url)

        wcivf_json = self.get_wcivf_json(wdiv_json)

        return wdiv_json, wcivf_json
