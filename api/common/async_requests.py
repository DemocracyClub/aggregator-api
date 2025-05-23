import asyncio
from json import JSONDecodeError
from typing import Dict

import httpx

client = httpx.AsyncClient(http2=True)


class UpstreamApiError(Exception):
    def __init__(self, response_dict: httpx.Response):
        try:
            self.message = {"error": response_dict.json().get("detail", "")}
        except JSONDecodeError:
            self.message = ""
        self.status = response_dict.status_code


async def retry_request(*args, **kwargs):
    retries = 1
    backoff_factor = 0.1
    status_codes = {502, 503, 504}

    for attempt in range(retries + 1):
        try:
            response = await client.get(*args, **kwargs)
            if response.status_code not in status_codes:
                return response
        except httpx.TransportError as e:
            if attempt >= retries:
                raise e

        if attempt < retries:
            await asyncio.sleep(backoff_factor * (2**attempt))

    return response


async def get_url(key, url_data, request_urls, raise_errors=True):
    response: httpx.Response = await retry_request(
        url=url_data["url"],
        params=url_data.get("params", {}),
        headers=url_data.get("headers", {}),
    )
    request_urls[key]["response"] = response
    if raise_errors:
        if request_urls[key]["response"].status_code >= 400:
            raise UpstreamApiError(request_urls[key]["response"])
        request_urls[key]["response"].raise_for_status()


async def async_get_urls(
    requst_urls, raise_errors=True
) -> Dict[str, httpx.Response]:
    await asyncio.gather(
        *[
            get_url(
                key, requst_urls[key], requst_urls, raise_errors=raise_errors
            )
            for key in requst_urls
        ]
    )
    if raise_errors:
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

    async def get_urls(self, raise_errors=True) -> dict:
        return await async_get_urls(
            self.request_dict, raise_errors=raise_errors
        )
