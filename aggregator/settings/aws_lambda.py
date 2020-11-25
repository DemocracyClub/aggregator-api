from .base import *  # noqa

DEBUG = True


ALLOWED_HOSTS = ["*"]

FORCE_SCRIPT_NAME = "/"
USE_X_FORWARDED_HOST = True

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "/tmp/db.sqlite3"}
}

AWS_S3_SECURE_URLS = False
AWS_S3_USE_SSL = True
AWS_S3_REGION_NAME = "eu-west-2"
AWS_QUERYSTRING_AUTH = False

# TODO: pull in something meaningful here
ZAPPA_STAGE = False
if ZAPPA_STAGE == "prod":
    AWS_STORAGE_BUCKET_NAME = "aggregator-api-prod-static"
    AWS_S3_CUSTOM_DOMAIN = "developers.democracyclub.org.uk"
else:
    AWS_STORAGE_BUCKET_NAME = "static-developers-dev-aws-ci-cd-test"
    AWS_S3_CUSTOM_DOMAIN = (
        "static-developers-dev-aws-ci-cd-test.s3-website.eu-west-2.amazonaws.com"
    )


MEDIAFILES_LOCATION = "media"
MEDIA_URL = "http://{}/{}/".format(AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = "aggregator.s3_lambda_storage.MediaStorage"

STATICFILES_LOCATION = "static"
STATIC_URL = "http://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
STATICFILES_STORAGE = "aggregator.s3_lambda_storage.StaticStorage"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.CachedFileFinder",
    "pipeline.finders.PipelineFinder",
)

PIPELINE["COMPILERS"] = ("aggregator.s3_lambda_storage.LambdaSASSCompiler",)  # noqa
