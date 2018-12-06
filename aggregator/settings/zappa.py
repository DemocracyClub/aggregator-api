from .base import *  # noqa

DEBUG = False

ZAPPA_STAGE = os.environ["STAGE"]
assert ZAPPA_STAGE in ("dev", "prod")

ALLOWED_HOSTS = [
    "vps1s53ua6.execute-api.eu-west-2.amazonaws.com",  # Dev
    "q2l5dijqu0.execute-api.eu-west-2.amazonaws.com",  # Prod
]

FORCE_SCRIPT_NAME = "/"
USE_X_FORWARDED_HOST = True

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": "/tmp/db.sqlite3"}
}

AWS_S3_SECURE_URLS = True
AWS_S3_USE_SSL = True
AWS_S3_REGION_NAME = "eu-west-2"
AWS_QUERYSTRING_AUTH = False

if ZAPPA_STAGE == "prod":
    AWS_STORAGE_BUCKET_NAME = "aggregator-api-prod-static"
    AWS_S3_CUSTOM_DOMAIN = "developers.democracyclub.org.uk"
else:
    AWS_STORAGE_BUCKET_NAME = "static-developers-dev.democracyclub.org.uk"
    AWS_S3_CUSTOM_DOMAIN = "devtest.democracyclub.org.uk"


MEDIAFILES_LOCATION = "media"
MEDIA_URL = "https://{}/{}/".format(AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = "aggregator.s3_lambda_storage.MediaStorage"

STATICFILES_LOCATION = "static"
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
STATICFILES_STORAGE = "aggregator.s3_lambda_storage.StaticStorage"

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
    "pipeline.finders.CachedFileFinder",
    "pipeline.finders.PipelineFinder",
)

PIPELINE["COMPILERS"] = ("aggregator.s3_lambda_storage.LambdaSASSCompiler",)  # noqa
