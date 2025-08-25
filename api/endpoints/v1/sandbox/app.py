from pathlib import Path

from mangum import Mangum
from starlette.applications import Starlette
from starlette.responses import FileResponse, Response
from starlette.routing import Route

from common.conf import settings
from common.middleware import MIDDLEWARE
from common.sentry_helper import init_sentry

init_sentry()


def sandbox_content(filename):
    path = Path(__file__).parent / f"sandbox-responses/{filename}.json"
    if not path.exists():
        raise FileNotFoundError()
    return path


async def sandbox_postcode(request):
    try:
        return FileResponse(
            sandbox_content(request.path_params["postcode"].upper())
        )
    except FileNotFoundError:
        return Response(status_code=404)


async def sandbox_address(request):
    try:
        return FileResponse(sandbox_content(request.path_params["uprn"]))
    except FileNotFoundError:
        return Response(status_code=404)


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
