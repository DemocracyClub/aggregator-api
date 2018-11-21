import asyncio
import aiohttp
from django.conf import settings


class ApiError(Exception):
    def __init__(self, status, message):
        self.status = status
        self.message = message


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

    params["utm_medium"] = "devs.DC API"
    headers = {"User-Agent": "devs.DC API"}
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, params=params, headers=headers) as response:
            body = await response.json()
            return {"url": url, "json": body, "status": response.status}


class ApiClient:
    def __init__(self):
        self.loop = get_event_loop()

    def __del__(self):
        try:
            self.loop.close()
        except Exception:
            pass

    def get_data_for_postcode(self, postcode):
        wdiv_url = f"{settings.WDIV_BASE_URL}postcode/{postcode}/"
        wdiv_params = {}
        if settings.WDIV_API_KEY:
            wdiv_params["auth_token"] = settings.WDIV_API_KEY
        wcivf_url = (
            f"{settings.WCIVF_BASE_URL}candidates_for_postcode/?postcode={postcode}"
        )

        responses = asyncio.gather(
            asyncio.ensure_future(fetch(wdiv_url, wdiv_params)),
            asyncio.ensure_future(fetch(wcivf_url)),
        )

        self.loop.run_until_complete(responses)

        wdiv_result = self.get_wdiv_result(responses.result())
        wcivf_result = self.get_wcivf_result(responses.result())

        if wdiv_result["status"] >= 400:
            raise ApiError(wdiv_result["status"], wdiv_result["json"]["detail"])
        if wcivf_result["status"] >= 400:
            raise ApiError(wcivf_result["status"], wcivf_result["json"]["detail"])

        return (wdiv_result["json"], wcivf_result["json"])

    def get_result_by_base_url(self, results, base_url):
        for r in results:
            if base_url in r["url"]:
                return r
        raise ApiError(500, "Internal Server Error")

    def get_wdiv_result(self, results):
        return self.get_result_by_base_url(results, settings.WDIV_BASE_URL)

    def get_wcivf_result(self, results):
        return self.get_result_by_base_url(results, settings.WCIVF_BASE_URL)

    def get_data_for_address(self, slug):
        wdiv_url = f"{settings.WDIV_BASE_URL}address/{slug}/"
        wdiv_params = {}
        if settings.WDIV_API_KEY:
            wdiv_params["auth_token"] = settings.WDIV_API_KEY

        wdiv_response = asyncio.ensure_future(fetch(wdiv_url, wdiv_params))
        self.loop.run_until_complete(wdiv_response)
        wdiv_result = wdiv_response.result()
        if wdiv_result["status"] >= 400:
            raise ApiError(wdiv_result["status"], wdiv_result["json"]["detail"])
        wdiv_json = wdiv_result["json"]

        if wdiv_json["ballots"]:
            ballot_ids = [b["ballot_paper_id"] for b in wdiv_json["ballots"]]
            wcivf_url = f'{settings.WCIVF_BASE_URL}candidates_for_ballots/?ballot_ids={",".join(ballot_ids)}'
        else:
            wcivf_url = f'{settings.WCIVF_BASE_URL}candidates_for_postcode/?postcode={wdiv_json["addresses"][0]["postcode"]}'

        wcivf_response = asyncio.ensure_future(fetch(wcivf_url))
        self.loop.run_until_complete(wcivf_response)
        wcivf_result = wcivf_response.result()
        if wcivf_result["status"] >= 400:
            raise ApiError(wcivf_result["status"], wcivf_result["json"]["detail"])
        wcivf_json = wcivf_result["json"]

        return wdiv_json, wcivf_json
