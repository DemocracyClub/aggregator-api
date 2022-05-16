from fastapi import FastAPI, Request
from mangum import Mangum

from stitcher import Stitcher
from upstream_api_client import WdivWcivfApiClient

app = FastAPI(
    docs_url=None
)


@app.get("/api/v2/postcode")
async def root(request: Request):
    client = WdivWcivfApiClient(request)
    wdiv, wcivf = await client.get_data_for_postcode("SE22 8DJ")

    stitcher = Stitcher(wdiv, wcivf, request)
    return stitcher.make_result_known_response()


handler = Mangum(app)
