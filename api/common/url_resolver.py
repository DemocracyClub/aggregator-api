import typing

from starlette.datastructures import URLPath
from starlette.routing import NoMatchFound, Route


class FakeRoute(Route):
    def __init__(
        self,
        path: str,
        *,
        methods: typing.Optional[typing.List[str]] = None,
        name: typing.Optional[str] = None,
        include_in_schema: bool = True,
    ) -> None:
        def _fake_endpoint():
            pass

        super().__init__(
            path,
            _fake_endpoint,
            methods=methods,
            name=name,
            include_in_schema=include_in_schema,
        )


ALL_ROUTES = {
    "v1/elections": [
        FakeRoute(
            "/api/v1/elections/{slug}/", methods=["GET"], name="single_election"
        ),
        FakeRoute("/api/v1/elections/", methods=["GET"], name="election_list"),
    ],
    "v1/voting_information": [
        FakeRoute(
            "/api/v1/postcode/{postcode}/", methods=["GET"], name="postcode"
        ),
        FakeRoute("/api/v1/address/{uprn}/", methods=["GET"], name="address"),
    ],
    "v1/sandbox": [
        FakeRoute(
            "/api/v1/sandbox/postcode/{postcode}/",
            methods=["GET"],
            name="sandbox_postcode",
        ),
        FakeRoute(
            "/api/v1/sandbox/address/{uprn}/",
            methods=["GET"],
            name="sandbox_address",
        ),
        FakeRoute(
            "/api/v1/sandbox/elections/",
            methods=["GET"],
            name="sandbox_election_list",
        ),
        FakeRoute(
            "/api/v1/sandbox/elections/{slug}/",
            methods=["GET"],
            name="sandbox_single_election",
        ),
    ],
}


def build_absolute_url(base_url: str, name: str, sandbox=False, **params):
    """
    Like Starlette's built in `url_for`, but not depending on the URL
    existing in the router.

    This allows for abstracting linking between endpoints (avoiding hard coding
    URLs throughout the codebase), but doesn't require all endpoints to be
    in the same router / app.

    """
    if sandbox:
        name = f"sandbox_{name}"

    # Reproduce the content of the routes lists in each app.py
    URLS = []
    for app_name, routes in ALL_ROUTES.items():
        URLS += routes

    match = None
    for url in URLS:
        if url.name == name:
            match = url.url_path_for(name, **params)
            break
    if not match:
        raise NoMatchFound(name, params)

    return str(URLPath(path=match).make_absolute_url(base_url=str(base_url)))
