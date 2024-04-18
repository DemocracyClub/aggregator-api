from common.conf import settings
from common.middleware import MIDDLEWARE
from common.sentry_helper import init_sentry
from election_views import (
    get_election_list,
    get_elections_for_postcode,
    get_elections_for_uprn,
    get_single_election,
)
from mangum import Mangum
from starlette.applications import Starlette
from starlette.routing import Route

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

handler = Mangum(app)
