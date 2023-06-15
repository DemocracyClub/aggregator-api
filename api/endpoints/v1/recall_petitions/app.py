from client import RecallPetitionApiClient
from common import settings
from common.middleware import MIDDLEWARE
from common.sentry_helper import init_sentry
from mangum import Mangum
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

init_sentry()


async def get_postcode(request: Request):
    postcode = request.path_params["postcode"].upper()
    client = RecallPetitionApiClient(request)
    result = client.get_data_for_postcode(postcode)
    return JSONResponse(result)


async def get_address(request: Request):
    uprn = request.path_params["uprn"]
    client = RecallPetitionApiClient(request)
    result = client.get_data_for_address(uprn)
    return JSONResponse(result)


routes = [
    Route(
        "/api/v1/recall_petitions/postcode/{postcode}/",
        get_postcode,
        methods=["GET"],
        name="recall_petitions_postcode",
    ),
    Route(
        "/api/v1/recall_petitions/address/{uprn}/",
        get_address,
        methods=["GET"],
        name="recall_petitions_address",
    ),
]

app = Starlette(debug=settings.DEBUG, routes=routes, middleware=MIDDLEWARE)

handler = Mangum(app)
