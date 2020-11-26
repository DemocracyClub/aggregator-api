from .base import *  # noqa

DEBUG = False
ALLOWED_HOSTS = ["*"]
FORCE_SCRIPT_NAME = "/Prod"
USE_X_FORWARDED_HOST = True

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "/tmp/db.sqlite3"}
}

AWS_S3_SECURE_URLS = False
AWS_S3_USE_SSL = True
AWS_S3_REGION_NAME = "eu-west-2"
AWS_QUERYSTRING_AUTH = False

AWS_STORAGE_BUCKET_NAME = "aggregator-api-production-static-assets-23fskj4t0a"
# AWS_S3_CUSTOM_DOMAIN = "developers.democracyclub.org.uk"
AWS_S3_CUSTOM_DOMAIN = f"{AWS_STORAGE_BUCKET_NAME}.s3-website.eu-west-2.amazonaws.com"

MEDIAFILES_LOCATION = "media"
MEDIA_URL = "http://{}/{}/".format(AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = "aggregator.s3_lambda_storage.MediaStorage"

PIPELINE_ENABLED = False
AWS_DEFAULT_ACL = "public-read"
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
