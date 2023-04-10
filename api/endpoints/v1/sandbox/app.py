from pathlib import Path

from common import settings
from common.middleware import MIDDLEWARE
from common.sentry_helper import init_sentry
from mangum import Mangum
from starlette.applications import Starlette
from starlette.responses import FileResponse
from starlette.routing import Route

init_sentry()


def sandbox_content(filename):
    return Path(__file__).parent / f"sandbox-responses/{filename}.json"


async def sandbox_postcode(request):
    return FileResponse(
        sandbox_content(request.path_params["postcode"].upper())
    )


async def sandbox_address(request):
    return FileResponse(sandbox_content(request.path_params["uprn"]))


routes = [
    Route(
        "/api/v1/sandbox/postcode/{postcode}/",
        sandbox_postcode,
        methods=["GET"],
        name="sandbox_postcode",
    ),
    Route(
        "/api/v1/sandbox/address/{uprn}/",
        sandbox_address,
        methods=["GET"],
        name="sandbox_address",
    ),
]
app = Starlette(debug=settings.DEBUG, routes=routes, middleware=MIDDLEWARE)

handler = Mangum(app)
