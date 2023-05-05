from common.async_requests import UpstreamApiError
from elections_api_client import WdivWcivfApiClient
from starlette.requests import Request
from starlette.responses import JSONResponse
from stitcher import Stitcher


def get_address(request: Request):
    uprn = request.path_params["uprn"]
    client = WdivWcivfApiClient(query_params=request.query_params)
    try:
        wdiv, wcivf = client.get_data_for_address(uprn)
    except UpstreamApiError as error:
        return JSONResponse(error.message, status_code=error.status)
    stitcher = Stitcher(wdiv, wcivf, request)
    return JSONResponse(stitcher.make_result_known_response())
