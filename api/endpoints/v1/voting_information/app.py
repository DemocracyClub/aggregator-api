from mangum import Mangum
from starlette.applications import Starlette

from starlette.routing import Route

from common.middleware import MIDDLEWARE
from postcode import get_postcode
from address import get_address

routes = [
    Route(
        "/api/v1/postcode/{postcode}/", get_postcode, methods=["GET"], name="postcode"
    ),
    Route("/api/v1/address/{uprn}/", get_address, methods=["GET"], name="address"),
]
app = Starlette(debug=True, routes=routes, middleware=MIDDLEWARE)

handler = Mangum(app)
