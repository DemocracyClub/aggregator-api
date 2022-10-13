import contextlib
import os

import anyio
from dc_logging_client import DCWidePostcodeLoggingClient
from mangum import Mangum
from starlette.applications import Starlette

from starlette.routing import Route

from common.middleware import MIDDLEWARE
from postcode import get_postcode
from address import get_address


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    FIREHOSE_ACCOUNT_ARN = os.environ.get("FIREHOSE_ACCOUNT_ARN", None)
    if FIREHOSE_ACCOUNT_ARN:
        firehose_args = dict(assume_role_arn=FIREHOSE_ACCOUNT_ARN)
    else:
        firehose_args = dict(fake=True)
    app.state.POSTCODE_LOGGER = DCWidePostcodeLoggingClient(**firehose_args)

    async with anyio.create_task_group() as app.task_group:
        yield


routes = [
    Route(
        "/api/v1/postcode/{postcode}/", get_postcode, methods=["GET"], name="postcode"
    ),
    Route("/api/v1/address/{uprn}/", get_address, methods=["GET"], name="address"),
]
app = Starlette(debug=True, routes=routes, middleware=MIDDLEWARE, lifespan=lifespan)

handler = Mangum(app)
