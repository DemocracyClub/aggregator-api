import os
import awsgi

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aggregator.settings")

application = get_wsgi_application()


def lambda_handler(event, context):
    return awsgi.response(
        application, event, context, base64_content_types={"image/png"}
    )
