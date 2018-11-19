import asyncio
import aiohttp
from django.conf import settings


def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


async def fetch(url):
    # TODO: set a custom user agent
    # TODO: set utm_ params
    timeout = aiohttp.ClientTimeout(total=10)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as response:
            print(url)
            response.raise_for_status()
            body = await response.json()
            return {"url": url, "json": body}


class ApiClient:
    def __init__(self):
        self.loop = get_event_loop()

    def __del__(self):
        try:
            self.loop.close()
        except Exception:
            pass

    def get_data_for_postcode(self, postcode):
        # TODO: API key for WDIV
        wdiv_url = f"{settings.WDIV_BASE_URL}postcode/{postcode}"
        wcivf_url = (
            f"{settings.WCIVF_BASE_URL}candidates_for_postcode/?postcode={postcode}"
        )

        responses = asyncio.gather(
            asyncio.ensure_future(fetch(wdiv_url)),
            asyncio.ensure_future(fetch(wcivf_url)),
        )

        self.loop.run_until_complete(responses)

        return (
            self.get_wdiv_result(responses.result()),
            self.get_wcivf_result(responses.result()),
        )

    def get_result_by_base_url(self, results, base_url):
        for r in results:
            if base_url in r["url"]:
                return r["json"]
        return None

    def get_wdiv_result(self, results):
        return self.get_result_by_base_url(results, settings.WDIV_BASE_URL)

    def get_wcivf_result(self, results):
        return self.get_result_by_base_url(results, settings.WCIVF_BASE_URL)

    def get_data_for_address(self, slug):
        # TODO: API key for WDIV
        wdiv_url = f"{settings.WDIV_BASE_URL}address/{slug}"

        wdiv_response = asyncio.ensure_future(fetch(wdiv_url))
        self.loop.run_until_complete(wdiv_response)

        wdiv_result = wdiv_response.result()["json"]
        if wdiv_result["ballots"]:
            ballot_ids = [b["ballot_paper_id"] for b in wdiv_result["ballots"]]
            wcivf_url = f'{settings.WCIVF_BASE_URL}candidates_for_ballots/?ballot_ids={",".join(ballot_ids)}'
        else:
            wcivf_url = f'{settings.WCIVF_BASE_URL}candidates_for_postcode/?postcode={wdiv_result["addresses"][0]["postcode"]}'

        wcivf_response = asyncio.ensure_future(fetch(wcivf_url))
        self.loop.run_until_complete(wcivf_response)

        return wdiv_result, wcivf_response.result()["json"]
