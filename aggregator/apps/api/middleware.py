import logging
import traceback
from django.conf import settings
from django.http import JsonResponse
from .errors import ApiError

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def process_exception(self, request, exception):
        if (
            not settings.DEBUG
            and "/sandbox" not in request.path
            and "/api" in request.path
        ):
            if isinstance(exception, ApiError):
                if exception.status >= 500:
                    logger.error(traceback.format_exc())
                return JsonResponse(
                    {"message": exception.message}, status=exception.status
                )
            logger.error(traceback.format_exc())
            return JsonResponse({"message": "Internal Server Error"}, status=500)

    def __call__(self, request):
        return self.get_response(request)
