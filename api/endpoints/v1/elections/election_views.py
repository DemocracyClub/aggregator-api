from dc_logging_client import DCWidePostcodeLoggingClient
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

    logger: DCWidePostcodeLoggingClient = request.app.state.POSTCODE_LOGGER
    entry = logger.entry_class(
        postcode=str(postcode),
        dc_product=logger.dc_product.aggregator_api,
        api_key=request.scope["api_user"].api_key,
        calls_devs_dc_api=False,
        **request.scope["utm_dict"],
    )
    logger.log(entry)

    data_helper = ElectionsForPostcodeHelper(postcode, request)
    response_data = await data_helper.build_response()
    # TODO: logging
    return JSONResponse(response_data)


async def get_elections_for_uprn(request: Request):
    postcode = request.path_params["postcode"].upper()
    uprn = request.path_params["uprn"]
    data_helper = ElectionsForPostcodeHelper(postcode, request, uprn=uprn)
    response_data = await data_helper.build_response()
    return JSONResponse(response_data)
