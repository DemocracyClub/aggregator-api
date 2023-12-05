import os

from django.core.mail import send_mail
from django.http import HttpRequest
from django.urls import reverse

from api_users.models import APIKey


def get_domain(request: HttpRequest):
    return os.environ.get("APP_DOMAIN", request.get_host())


def send_new_key_notification(request, api_key: APIKey):
    user_admin_url = request.build_absolute_uri(
        reverse(
            "admin:api_users_customuser_change",
            kwargs={"object_id": api_key.user_id},
        )
    )

    message = f"""
    {api_key.user.name} has just created a new API key called {api_key.name}.

    This is a {api_key.key_type} key.

    They said the usage reason was:

    > "{api_key.usage_reason}"

    You can contact {api_key.user.name} on {api_key.user.email}.

    Or, you can view the user in the admin interface here: {user_admin_url}

    """
    send_mail(
        "New email key creation",
        message,
        "developers@democracyclub.org.uk",
        ["hello@democracyclub.org.uk"],
        fail_silently=True,
    )
    return message
