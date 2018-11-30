import logging

logger = logging.getLogger(__name__)


class LoggerMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if (
            response.status_code >= 500
            and "/sandbox" not in request.path
            and "/api" in request.path
        ):
            logger.error(f"{response.status_code} - {response.content}")
        return response
