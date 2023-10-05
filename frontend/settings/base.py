import contextlib
import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, "apps"))
sys.path.insert(0, os.path.join(BASE_DIR.parent, "api"))
sys.path.insert(0, os.path.join(BASE_DIR.parent, "api/endpoints/v1"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SECRET_KEY", None)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "apiblueprint_view",
    "pipeline",
    "dc_design_system",
    "dc_utils",
]
PROJECT_APPS = ["api_docs.v1"]
INSTALLED_APPS += PROJECT_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "frontend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dc_utils.context_processors.dc_django_utils",
            ]
        },
    }
]

WSGI_APPLICATION = "frontend.wsgi.application"


# Database
# https://docs.djangoproject.com/en/1.11/ref/settings/#databases

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3"}}


# Password validation
# https://docs.djangoproject.com/en/1.11/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.11/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.11/howto/static-files/

from dc_utils.settings.pipeline import *  # noqa
from dc_utils.settings.pipeline import get_pipeline_settings  # noqa

PIPELINE = get_pipeline_settings(extra_css=["scss/styles.scss"])

import dc_design_system  # noqa

PIPELINE["SASS_ARGUMENTS"] += (
    " -I " + dc_design_system.DC_SYSTEM_PATH + "/system"
)

SASS_INCLUDE_PATHS = [dc_design_system.DC_SYSTEM_PATH + "/system"]
STATIC_ROOT = os.path.join(BASE_DIR, "static_files")
STATIC_URL = "/static/"
STATICFILES_DIRS = (os.path.join(BASE_DIR, "assets"),)

SITE_TITLE = "Democracy Club Developers"


# CorsMiddleware config
CORS_ORIGIN_ALLOW_ALL = True
CORS_URLS_REGEX = r"^/api/.*$"
CORS_ALLOW_METHODS = ("GET", "OPTIONS")

from .constants import *  # noqa


sentry_dsn = os.environ.get("SENTRY_DSN", None)
if sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=sentry_dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=0,
        send_default_pii=False,
    )


# Lambda: https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-runtime
# CircleCI: https://circleci.com/docs/2.0/env-vars/#built-in-environment-variables
# Make: https://docs.oracle.com/cd/E19504-01/802-5880/makeattapp-21/index.html
def is_local_dev():
    vars_to_check = ["AWS_LAMBDA_FUNCTION_NAME", "CI", "MAKEFLAGS"]
    return not any(ev in os.environ for ev in vars_to_check)


# .local.py overrides all the common settings.
if is_local_dev():
    print(
        "Found nothing to indicate this is NOT an local development environment; including settings/local.py"
    )  # FIXME: log?
    with contextlib.suppress(ImportError):
        from .local import *  # noqa
