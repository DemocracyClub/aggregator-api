from dc_logging_client import DCWidePostcodeLoggingClient
from elections_api_client import WdivWcivfApiClient
from starlette.requests import Request
from starlette.responses import JSONResponse
from stitcher import Stitcher

from common.async_requests import UpstreamApiError


def get_address(request: Request):
    uprn: str = request.path_params["uprn"]
    logger: DCWidePostcodeLoggingClient = request.app.state.POSTCODE_LOGGER
    client = WdivWcivfApiClient(query_params=request.query_params)
    try:
        wdiv, wcivf = client.get_data_for_address(uprn)
    except UpstreamApiError as error:
        return JSONResponse(error.message, status_code=error.status)
    stitcher = Stitcher(wdiv, wcivf, request)
    result = stitcher.make_result_known_response()

    has_ballot = any(date.get("ballots") for date in result.get("dates", []))

    # Try and get the postcode from the postcode location
    postcode_location = result.get("postcode_location", {})
    properties = postcode_location.get("properties", {})
    postcode = properties.get("postcode", None)

    logger.log(
        logger.entry_class(
            postcode=str(postcode),
            dc_product=logger.dc_product.aggregator_api,
            api_key=request.scope["api_user"].api_key,
            calls_devs_dc_api=False,
            had_election=has_ballot,
            **request.scope["utm_dict"],
        )
    )

    return JSONResponse(result)
