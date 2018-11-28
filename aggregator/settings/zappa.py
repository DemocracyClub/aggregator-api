from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = [
    "vps1s53ua6.execute-api.eu-west-2.amazonaws.com",
]

FORCE_SCRIPT_NAME = '/'
USE_X_FORWARDED_HOST = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "/tmp/db.sqlite3",
    }
}

TMP_ASSETS_ROOT = "/tmp/assets_root"
STATIC_ROOT = '/tmp/static_root/'

# Make the tmp static dirs whenever django is started
os.makedirs(TMP_ASSETS_ROOT, exist_ok=True)
os.makedirs(STATIC_ROOT, exist_ok=True)

AWS_S3_SECURE_URLS = True
# AWS_S3_HOST = 's3-eu-west-2.amazonaws.com'
AWS_S3_USE_SSL = True
AWS_S3_REGION_NAME = "eu-west-2"
AWS_STORAGE_BUCKET_NAME = "static-developers-dev.democracyclub.org.uk"
AWS_S3_CUSTOM_DOMAIN = "devtest.democracyclub.org.uk"

MEDIAFILES_LOCATION = 'media'
MEDIA_URL = "https://{}/{}/".format(AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'aggregator.s3_lambda_storage.MediaStorage'

STATICFILES_LOCATION = 'static'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)
STATICFILES_STORAGE = 'aggregator.s3_lambda_storage.StaticStorage'

STATICFILES_FINDERS = (
    'aggregator.s3_lambda_storage.ReadOnlySourceFileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'pipeline.finders.CachedFileFinder',
    'pipeline.finders.PipelineFinder',
)

# Used by ReadOnlySourceFileSystemFinder
READ_ONLY_PATHS = (
    (os.path.join(BASE_DIR, "assets"), TMP_ASSETS_ROOT),  # noqa
)


PIPELINE['COMPILERS'] = ('aggregator.s3_lambda_storage.LambdaSASSCompiler', )   # noqa
