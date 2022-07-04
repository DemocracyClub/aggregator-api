from starlette.requests import Request
from starlette.responses import JSONResponse

from voting_information_api_client import EEApiClient


async def get_election_list(request: Request):
    client = EEApiClient(request.base_url)
    result = await client.get_election_list(request.query_params)
    return JSONResponse(result)


async def get_single_election(request: Request):
    client = EEApiClient(request.base_url)
    result = await client.get_single_election(request.path_params["slug"])
    return JSONResponse(result)
