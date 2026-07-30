import httpx
import pytest
from common.async_requests import (
    AsyncRequester,
    UpstreamApiError,
    retry_request,
)


@pytest.mark.asyncio
async def test_async_requester(respx_mock):
    wcivf = respx_mock.get("https://whocanivotefor.co.uk/").mock(
        return_value=httpx.Response(200, content="WhoCanIVoteFor")
    )
    wdiv = respx_mock.get("https://wheredoivote.co.uk/").mock(
        return_value=httpx.Response(200, content="WhereDoIVote")
    )

    async_requester = AsyncRequester(
        request_dict={
            "wcivf": {"url": "https://whocanivotefor.co.uk/"},
            "wdiv": {"url": "https://wheredoivote.co.uk/"},
        }
    )
    await async_requester.get_urls()
    assert wcivf.called
    assert wdiv.called
    assert (
        async_requester.request_dict["wcivf"]["response"].text
        == "WhoCanIVoteFor"
    )
    assert (
        async_requester.request_dict["wdiv"]["response"].text == "WhereDoIVote"
    )


@pytest.mark.asyncio
async def test_async_requester_with_500_error_raises(respx_mock):
    respx_mock.get("https://whocanivotefor.co.uk/").mock(
        return_value=httpx.Response(500)
    )
    respx_mock.get("https://wheredoivote.co.uk/").mock(
        return_value=httpx.Response(200, content="WhereDoIVote")
    )

    async_requester = AsyncRequester(
        request_dict={
            "wcivf": {"url": "https://whocanivotefor.co.uk/"},
            "wdiv": {"url": "https://wheredoivote.co.uk/"},
        }
    )
    with pytest.raises(UpstreamApiError) as error:
        await async_requester.get_urls()

    assert "500 Internal Server Error" in str(error.value)


@pytest.mark.asyncio
async def test_retry_request_success_on_first_attempt(respx_mock):
    respx_mock.get("https://example.com/").mock(
        return_value=httpx.Response(200, content="Success")
    )

    response = await retry_request(url="https://example.com/")
    assert response.status_code == 200
    assert response.text == "Success"


@pytest.mark.asyncio
async def test_retry_request_success_after_retries(respx_mock):
    call_count = 0

    def mock_response(request):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            return httpx.Response(502)
        return httpx.Response(200, content="Recovered")

    respx_mock.get("https://example.com/").mock(side_effect=mock_response)

    response = await retry_request(url="https://example.com/")
    assert call_count == 2
    assert response.status_code == 200
    assert response.text == "Recovered"


@pytest.mark.asyncio
async def test_retry_request_all_fails_transport_error(respx_mock):
    respx_mock.get("https://example.com/").mock(
        side_effect=httpx.TransportError
    )

    with pytest.raises(httpx.TransportError):
        await retry_request(url="https://example.com/")


@pytest.mark.asyncio
async def test_retry_request_all_fails_502(respx_mock):
    respx_mock.get("https://example.com/").mock(
        return_value=httpx.Response(502)
    )

    response = await retry_request(url="https://example.com/")
    assert response.status_code == 502
