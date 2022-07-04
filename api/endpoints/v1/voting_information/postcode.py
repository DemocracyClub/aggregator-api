from starlette.requests import Request
from starlette.responses import JSONResponse

from stitcher import Stitcher
from elections_api_client import WdivWcivfApiClient


async def get_postcode(request: Request):
    postcode = request.path_params["postcode"]
    client = WdivWcivfApiClient()
    wdiv, wcivf = await client.get_data_for_postcode(postcode)
    stitcher = Stitcher(wdiv, wcivf, request)

    if not wdiv["polling_station_known"] and len(wdiv["addresses"]) > 0:
        result = stitcher.make_address_picker_response()
    else:
        result = stitcher.make_result_known_response()

    return JSONResponse(result)
