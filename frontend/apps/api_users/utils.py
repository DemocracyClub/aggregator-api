import os

from django.http import HttpRequest


def get_domain(request: HttpRequest):
    return os.environ.get("APP_DOMAIN", request.get_host())
