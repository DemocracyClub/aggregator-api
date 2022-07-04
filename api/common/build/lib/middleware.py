from starlette.datastructures import Headers
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware


class ForwardedForMiddleware:
    def __init__(
        self,
        app,
    ):
        self.app = app

    async def __call__(self, scope, receive, send):
        headers = Headers(scope=scope)
        forwarded_for = headers.get("x-forwarded-host", "").split(":")[0].encode()
        if forwarded_for:
            for i, header in enumerate(scope["headers"]):
                if header[0] == b"host":
                    scope["headers"].pop(i)
            scope["headers"].append((b"host", forwarded_for))
        await self.app(scope, receive, send)


MIDDLEWARE = [
    Middleware(ForwardedForMiddleware),
    Middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_headers=["Token", "Origin", "X-Requested-With"],
    ),
]
