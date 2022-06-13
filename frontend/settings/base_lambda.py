from boto3 import Session

from .base import *  # noqa
import os

ALLOWED_HOSTS = ["*"]
DEBUG = os.environ.get("DEBUG", False)

WHITENOISE_AUTOREFRESH = False
WHITENOISE_STATIC_PREFIX = "/static/"

PIPELINE["PIPELINE_ENABLED"] = os.environ.get("PIPELINE_ENABLED", False)  # noqa
PIPELINE["PIPELINE_COLLECTOR_ENABLED"] = False  # noqa

if os.environ.get("APP_IS_BEHIND_CLOUDFRONT", False) in [True, "true", "True", "TRUE"]:
    USE_X_FORWARDED_HOST = True
    STATIC_URL = WHITENOISE_STATIC_PREFIX
else:
    USE_X_FORWARDED_HOST = False
    FORCE_SCRIPT_NAME = "/Prod"
    STATIC_URL = FORCE_SCRIPT_NAME + WHITENOISE_STATIC_PREFIX

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "HOST": os.environ.get("DATABASE_HOST"),
        "USER": "postgres",
        "PORT": "5432",
        "NAME": os.environ.get("POSTGRES_DATABASE_NAME"),
        "PASSWORD": os.environ.get("DATABASE_PASS"),
    }
}

AWS_S3_SECURE_URLS = False
AWS_S3_USE_SSL = True
AWS_S3_REGION_NAME = "eu-west-2"
AWS_QUERYSTRING_AUTH = False

AWS_STORAGE_BUCKET_NAME = os.environ.get(
    "AWS_STORAGE_BUCKET_NAME", "aggregator-api-static-assets-development-7e3eabce9c"
)
AWS_S3_CUSTOM_DOMAIN = (
    f"{AWS_STORAGE_BUCKET_NAME}.s3-website.{AWS_S3_REGION_NAME}.amazonaws.com"
)

MEDIAFILES_LOCATION = "media"
MEDIA_URL = "http://{}/{}/".format(AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = "frontend.s3_lambda_storage.MediaStorage"

AWS_DEFAULT_ACL = "public-read"
STATICFILES_LOCATION = "static"
STATICFILES_STORAGE = "frontend.s3_lambda_storage.StaticStorage"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.CachedFileFinder",
    "pipeline.finders.PipelineFinder",
    "pipeline.finders.ManifestFinder",
)

PIPELINE["COMPILERS"] = ("frontend.s3_lambda_storage.LambdaSASSCompiler",)  # noqa

if os.environ.get("AWS_EXECUTION_ENV"):
    logger_boto3_session = Session(region_name="eu-west-2")

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "aws": {
                # you can add specific format for aws here
                # if you want to change format, you can read:
                #    https://stackoverflow.com/questions/533048/how-to-log-source-file-name-and-line-number-in-python/44401529
                # "format": "%(asctime)s [%(levelname)-8s] [ENV: %(env)s] %(message)s [%(pathname)s:%(lineno)d]",
                "format": "%(asctime)s [%(levelname)-8s] %(message)s [%(pathname)s:%(lineno)d]",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            }
        },
        "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "aws"}},
        "loggers": {
            "console": {"level": "INFO", "handlers": ["console"], "propogate": False}
        },
    }
