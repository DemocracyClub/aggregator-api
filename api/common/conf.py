import os

import boto3
from common.auth_models import ApiPlan

_s3_client_cache = None


def get_s3_client():
    global _s3_client_cache
    if _s3_client_cache is None:
        _s3_client_cache = boto3.client("s3")
    return _s3_client_cache


class BaseSettings:
    def __init__(self):
        self.DC_ENVIRONMENT = os.environ.get("DC_ENVIRONMENT", None)

        self.USER_AGENT = os.environ.get("API_USER_AGENT", "devs.DC API")
        self.WDIV_BASE_URL = "https://wheredoivote.co.uk/api/beta/"
        self.WDIV_API_KEY = os.environ.get("WDIV_API_KEY", None)
        self.EE_BASE_URL = "https://elections.democracyclub.org.uk/api/"

        self.WCIVF_BASE_URL = "https://whocanivotefor.co.uk/api/"
        self.WCIVF_BALLOT_CACHE_URL = (
            "https://wcivf-ballot-cache.s3.eu-west-2.amazonaws.com/ballot_data/"
        )

        # Only try to use the S3 Client if we think we're deployed
        self.S3_CLIENT_ENABLED = os.environ.get(
            "S3_CLIENT_ENABLED", bool(self.DC_ENVIRONMENT)
        )

        if self.S3_CLIENT_ENABLED:
            self.S3_CLIENT = get_s3_client()

        self.LOCAL_DATA_PATH = os.environ.get("LOCAL_STATIC_DATA_PATH", None)

        self.RECALL_PETITION_ENABLED = True
        self.RECALL_DATA_KEY_PREFIX = os.environ.get(
            "RECALL_DATA_KEY_PREFIX", "blackpool-south.2024-03/"
        )

        self.ELECTIONS_DATA_PATH = "s3://pollingstations.private.data/addressbase/2024-05-01/uprn-to-ballots-outcodes"

        self.DEBUG = bool(int(os.environ.get("DEBUG", "0")))

        self.API_PLANS = {
            "hobbyists": ApiPlan(
                value="hobbyists", label="Hobbyists", request_per_day=1_000
            ),
            "standard": ApiPlan(
                value="standard", label="Standard", request_per_day=10_000
            ),
            "enterprise": ApiPlan(
                value="enterprise", label="Enterprise", request_per_day=0
            ),
        }
        self.ALWAYS_INCLUDE_CURRENT = False


settings = BaseSettings()
