import os

from address import get_address
from common.conf import settings
from common.middleware import MIDDLEWARE
from common.sentry_helper import init_sentry
from dc_logging_client import DCWidePostcodeLoggingClient
from mangum import Mangum
from postcode import get_postcode
from starlette.applications import Starlette
from starlette.routing import Route

init_sentry()


def init_logger(app):
    LOGGER_ARN = os.environ.get("LOGGER_ARN", None)
    if LOGGER_ARN:
        firehose_args = {"function_arn": LOGGER_ARN}
    else:
        firehose_args = {"fake": True}
    app.state.POSTCODE_LOGGER = DCWidePostcodeLoggingClient(**firehose_args)
    return app


routes = [
    Route(
        "/api/v1/postcode/{postcode}/",
        get_postcode,
        methods=["GET"],
        name="postcode",
    ),
    Route(
        "/api/v1/address/{uprn}/", get_address, methods=["GET"], name="address"
    ),
]
app = Starlette(
    debug=settings.DEBUG,
    routes=routes,
    middleware=MIDDLEWARE,
)
init_logger(app)

handler = Mangum(app, lifespan="off")
