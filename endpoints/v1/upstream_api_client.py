from collections import namedtuple
from urllib.parse import urlparse
import asyncio
import aiohttp
import httpx

WDIV_BASE_URL = "http://wheredoivote.co.uk"
WCIVF_BASE_URL = "http://whocanivotefor.co.uk"
EE_BASE_URL = "https://elections.democracyclub.org.uk"


class UpstreamApiError(Exception):
    def __init__(self, message, status):
        self.message = message
        self.status = status


def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


async def fetch(url, params=None):
    if not params:
        params = {}

    headers = {"Accept": "application/json"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params, headers=headers) as response:
            body = await response.json()
            return {"url": url, "json": body, "status": response.status}


Request = namedtuple("Request", ["url", "params"])


def get_future(url, params):
    return asyncio.ensure_future(fetch(url, params))


def proxy_single_request(loop, request):
    response = get_future(request.url, request.params)
    loop.run_until_complete(response)
    result = response.result()
    if result["status"] >= 400:
        raise UpstreamApiError(result["json"]["detail"], result["status"])
    return result


def proxy_multiple_requests(loop, *requests):
    futures = [get_future(r.url, r.params) for r in requests]
    responses = asyncio.gather(*futures)
    loop.run_until_complete(responses)
    return responses.result()


class AsyncApiClient:
    def __init__(self, request):
        self.loop = get_event_loop()
        self.request = request


class WdivWcivfApiClient(AsyncApiClient):
    @property
    def wdiv_params(self):
        params = {"all_future_ballots": 1, "utm_medium": "settings.USER_AGENT"}
        params["auth_token"] = "8bf1538def32429ed10a2badba000bc455a75154"
        return params

    @property
    def wcivf_params(self):
        return {"utm_medium": "settings.USER_AGENT"}


    async def getURL(self, session, url):
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response

    async def get_data_for_postcode(self, postcode):
        wdiv_url = f"{WDIV_BASE_URL}/api/beta/postcode/{postcode}/?{self.wdiv_params}"
        wcivf_url = (
            f"{WCIVF_BASE_URL}/api/candidates_for_postcode/?postcode={postcode}"
        )

        async with httpx.AsyncClient() as session:
            wdiv_result, wcivf_result = await asyncio.gather(self.getURL(session, wdiv_url), self.getURL(session, wcivf_url))


        if wdiv_result.status_code >= 400:
            raise UpstreamApiError(wdiv_result.json()["detail"], wdiv_result.status_code)
        if wcivf_result.status_code >= 400:
            raise UpstreamApiError(
                wcivf_result.json()["detail"], wcivf_result.status_code
            )

        return (wdiv_result.json(), wcivf_result.json())

    def get_result_by_base_url(self, results, base_url):
        for r in results:
            if base_url in r["url"]:
                return r
        raise UpstreamApiError("Internal Server Error", 500)

    def get_wdiv_result(self, results):
        return self.get_result_by_base_url(results, WDIV_BASE_URL)

    def get_wcivf_result(self, results):
        return self.get_result_by_base_url(results, WCIVF_BASE_URL)

    def get_data_for_address(self, slug):
        wdiv_url = f"{WDIV_BASE_URL}address/{slug}/"

        wdiv_result = proxy_single_request(
            self.loop, Request(wdiv_url, self.wdiv_params)
        )
        wdiv_json = wdiv_result["json"]

        if wdiv_json["ballots"]:
            ballot_ids = [b["ballot_paper_id"] for b in wdiv_json["ballots"]]
            wcivf_url = f'{WCIVF_BASE_URL}candidates_for_ballots/?ballot_ids={",".join(ballot_ids)}'
        else:
            wcivf_url = f'{WCIVF_BASE_URL}candidates_for_postcode/?postcode={wdiv_json["addresses"][0]["postcode"]}'

        wcivf_result = proxy_single_request(
            self.loop, Request(wcivf_url, self.wcivf_params)
        )
        wcivf_json = wcivf_result["json"]

        return wdiv_json, wcivf_json


class EEApiClient(AsyncApiClient):
    def clean_query_params(self, params):
        """
        Take a django QueryDict object and return another QueryDict
        containing only the specified keys.

        We should use this both:
        - before passing a query string from devs.DC to EE and
        - before passing a URL with a query string from EE
          back to the devs.DC user.

        There are several things this acheives:
        1. There are some params that the devs.DC API accepts
           that we don't want to pass through to the EE API (e.g: auth_token)
        2. There are some params supported by the EE API
           that we don't want to expose to dev.DC users (e.g: postcode)
        3. In future, if we wanted to pass additional params to EE
           (e.g: a tracking param or API key, like we do with WDIV),
           they'll come back reflected in the next/previous URLs.
           Cleaning prevents us exposing those params to the devs.DC user.
        """

        return params

    def get_single_election(self, slug):
        ee_url = f"{EE_BASE_URL}elections/{slug}/"
        ee_result = proxy_single_request(self.loop, Request(ee_url, None))
        return self.filter_single_election(ee_result["json"])

    def get_election_list(self, query_dict):
        ee_url = f"{EE_BASE_URL}elections/"
        ee_result = proxy_single_request(
            self.loop,
            Request(ee_url, dict(self.clean_query_params(query_dict).items())),
        )
        return self.filter_election_list(ee_result["json"])

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
                q = parsed_url.query
                base = self.request.build_absolute_uri("elections/")
                response[key] = f"{base}?{q.urlencode()}"

        # list of election objects
        response["results"] = [
            self.filter_single_election(election) for election in response["results"]
        ]

        return response
