import contextlib
import os

import anyio
from address import get_address
from common.middleware import MIDDLEWARE
from dc_logging_client import DCWidePostcodeLoggingClient
from mangum import Mangum
from postcode import get_postcode
from starlette.applications import Starlette
from starlette.routing import Route


@contextlib.asynccontextmanager
async def lifespan(app: Starlette):
    FIREHOSE_ACCOUNT_ARN = os.environ.get("FIREHOSE_ACCOUNT_ARN", None)
    if FIREHOSE_ACCOUNT_ARN:
        firehose_args = {"assume_role_arn": FIREHOSE_ACCOUNT_ARN}
    else:
        firehose_args = {"fake": True}
    app.state.POSTCODE_LOGGER = DCWidePostcodeLoggingClient(**firehose_args)

    async with anyio.create_task_group() as app.task_group:
        yield


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
    debug=True, routes=routes, middleware=MIDDLEWARE, lifespan=lifespan
)

handler = Mangum(app)
