import asyncio
from json import JSONDecodeError
from typing import Dict

import httpx


class UpstreamApiError(Exception):
    def __init__(self, response_dict: httpx.Response):
        try:
            self.message = {"error": response_dict.json().get("detail", "")}
        except JSONDecodeError:
            self.message = ""
        self.status = response_dict.status_code


async def get_url(key, url_data, request_urls):
    async with httpx.AsyncClient(http2=True) as client:
        response: httpx.Response = client.get(
            url=url_data["url"],
            params=url_data.get("params", {}),
            headers=url_data.get("headers", {}),
        )
        request_urls[key]["response"] = await response
        if request_urls[key]["response"].status_code >= 400:
            raise UpstreamApiError(request_urls[key]["response"])
        request_urls[key]["response"].raise_for_status()


async def async_get_urls(requst_urls) -> Dict[str, httpx.Response]:
    await asyncio.gather(
        *[get_url(key, requst_urls[key], requst_urls) for key in requst_urls]
    )

    for url, result in requst_urls.items():
        if result["response"].status_code >= 400:
            raise UpstreamApiError(result)
    return requst_urls


class AsyncRequester:
    """
    Used HTTPX and async to request URLs in parallel

    Pass in a dict with the following structure:

    {
        "key1": {
            "url": "https://example.com/url1/",
            "params": {},
            "headers": {}
        },
        "key2": {
            "url": "https://example.com/url2/",
            "params": {},
            "headers": {}
        }
    }

    An async request for each URL will be started, and when they're all complete
    the dict will be returned with `response` objects:

    {
        "key1": {
            "url": "https://example.com/url1/",
            "params": {},
            "headers": {},
            "response": <httpx response object>
        },
        "key2": {
            "url": "https://example.com/url2/",
            "params": {},
            "headers": {},
            "response": <httpx response object>
        }
    }

    """

    USER_AGENT = "devs.DC API"

    def __init__(self, request_dict: Dict):
        self.request_dict = request_dict

    @property
    def get_default_headers(self):
        return {"Accept": "application/json", "User-Agent": self.USER_AGENT}

    def add_default_headers(self):
        for key, value in self.request_dict.items():
            headers = value.get("headers", {})
            headers.update(self.get_default_headers)

    async def get_urls(self) -> dict:
        return await async_get_urls(self.request_dict)
