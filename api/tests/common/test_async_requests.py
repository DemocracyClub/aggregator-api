import httpx
import pytest
from common.async_requests import AsyncRequester, UpstreamApiError


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
