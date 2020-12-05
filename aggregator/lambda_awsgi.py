import awsgi
import whoops_i_typed_the_wrong_name_here_fixme

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()


def lambda_handler(event, context):
    print(whoops_i_typed_the_wrong_name_here_fixme.an_export)
    return awsgi.response(
        application,
        event,
        context,
        base64_content_types={"image/png", "image/jpeg", "image/x-icon"},
    )
