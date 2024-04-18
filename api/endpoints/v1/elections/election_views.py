from starlette.requests import Request
from starlette.responses import JSONResponse
from static_elections_client import ElectionsForPostcodeHelper
from voting_information_api_client import EEApiClient


async def get_election_list(request: Request):
    client = EEApiClient(request.base_url)
    result = await client.get_election_list(request.query_params)
    return JSONResponse(result)


async def get_single_election(request: Request):
    client = EEApiClient(request.base_url)
    result = await client.get_single_election(request.path_params["slug"])
    return JSONResponse(result)


async def get_elections_for_postcode(request: Request):
    postcode = request.path_params["postcode"].upper()
    data_helper = ElectionsForPostcodeHelper(postcode)
    response_data = await data_helper.build_response()
    # TODO: logging
    return JSONResponse(response_data)


async def get_elections_for_uprn(request: Request):
    return JSONResponse("")
