import httpx
from common import settings
from common.async_requests import AsyncRequester
from httpx import QueryParams

# WDIV_BASE_URL = "http://wheredoivote.co.uk"
# WCIVF_BASE_URL = "https://whocanivotefor.co.uk"
# EE_BASE_URL = "https://elections.democracyclub.org.uk"


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
        wcivf_url = f"{settings.WCIVF_BASE_URL}candidates_for_postcode/?postcode={postcode}"
        request_urls = {"wdiv": {"url": wdiv_url}, "wcivf": {"url": wcivf_url}}
        requester = AsyncRequester(request_dict=request_urls)
        # This can raise a UpstreamApiError
        responses: dict = await requester.get_urls()

        wdiv_result: httpx.Response = responses["wdiv"]["response"]
        wcivf_result: httpx.Response = responses["wcivf"]["response"]

        return wdiv_result.json(), wcivf_result.json()

    async def get_data_for_address(self, slug):
        wdiv_url = f"{settings.WDIV_BASE_URL}address/{slug}/"

        request_urls = {"wdiv": {"url": wdiv_url, "params": self.wdiv_params}}

        # Async has no value here as it's a single URL, but it's a consistent
        # interface, so we may as well use it
        requester = AsyncRequester(request_dict=request_urls)
        # This can raise a UpstreamApiError
        responses = await requester.get_urls()
        wdiv_json = responses["wdiv"]["response"].json()

        wcivf_params = self.wcivf_params
        if wdiv_json["ballots"]:
            ballot_ids = [b["ballot_paper_id"] for b in wdiv_json["ballots"]]
            wcivf_url = f"{settings.WCIVF_BASE_URL}candidates_for_ballots/"
            wcivf_params = wcivf_params.merge(
                {"ballot_ids": ",".join(ballot_ids)}
            )
        else:
            wcivf_url = f"{settings.WCIVF_BASE_URL}candidates_for_postcode/"
            wcivf_params = wcivf_params.merge(
                {"postcode": wdiv_json["addresses"][0]["postcode"]}
            )

        request_urls = {"wcivf": {"url": wcivf_url, "params": wcivf_params}}
        # Async has no value here as it's a single URL, but it's a consistent
        # interface so we may as well use it
        requester = AsyncRequester(request_dict=request_urls)
        # This can raise a UpstreamApiError
        responses = await requester.get_urls()
        wcivf_json = responses["wcivf"]["response"].json()

        return wdiv_json, wcivf_json
