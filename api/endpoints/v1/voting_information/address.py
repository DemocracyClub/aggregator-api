from elections_api_client import WdivWcivfApiClient
from starlette.requests import Request
from starlette.responses import JSONResponse
from stitcher import Stitcher


async def get_address(request: Request):
    uprn = request.path_params["uprn"]
    client = WdivWcivfApiClient()
    wdiv, wcivf = await client.get_data_for_address(uprn)
    stitcher = Stitcher(wdiv, wcivf, request)
    return JSONResponse(stitcher.make_result_known_response())
