import os

from dc_logging_client import DCWidePostcodeLoggingClient
from election_views import (
    get_election_list,
    get_elections_for_postcode,
    get_elections_for_uprn,
    get_single_election,
)
from mangum import Mangum
from starlette.applications import Starlette
from starlette.routing import Route

from common.conf import settings
from common.middleware import MIDDLEWARE
from common.sentry_helper import init_sentry


def init_logger(app):
    # TODO: DRY this up (see also voting_information.app
    LOGGER_ARN = os.environ.get("LOGGER_ARN", None)
    if LOGGER_ARN:
        firehose_args = {"function_arn": LOGGER_ARN}
    else:
        firehose_args = {"fake": True}
    app.state.POSTCODE_LOGGER = DCWidePostcodeLoggingClient(**firehose_args)
    return app


init_sentry()

routes = [
    Route(
        "/api/v1/elections/{slug}/",
        get_single_election,
        methods=["GET"],
        name="single_election",
    ),
    Route(
        "/api/v1/elections/",
        get_election_list,
        methods=["GET"],
        name="election_list",
    ),
    Route(
        "/api/v1/elections/postcode/{postcode}/",
        get_elections_for_postcode,
        methods=["GET"],
        name="elections_for_postcode",
    ),
    Route(
        "/api/v1/elections/postcode/{postcode}/{uprn}/",
        get_elections_for_uprn,
        methods=["GET"],
        name="elections_for_uprn",
    ),
]
app = Starlette(debug=settings.DEBUG, routes=routes, middleware=MIDDLEWARE)

init_logger(app)

handler = Mangum(app)
