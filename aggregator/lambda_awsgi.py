import awsgi

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()


def lambda_handler(event, context):
    # FIXME: Remove this and figure out how to sort at the Lambda / API gateway level
    event["path"] = event.get("path").replace("%20", " ")

    return awsgi.response(
        application,
        event,
        context,
        base64_content_types={"image/png", "image/jpeg", "image/x-icon"},
    )
