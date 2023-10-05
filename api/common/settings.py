import os

from common.auth_models import ApiPlan

USER_AGENT = os.environ.get("API_USER_AGENT", "devs.DC API")
WDIV_API_KEY = os.environ.get("WDIV_API_KEY", None)

WDIV_BASE_URL = "https://wheredoivote.co.uk/api/beta/"
WCIVF_BASE_URL = "https://whocanivotefor.co.uk/api/"
WCIVF_BALLOT_CACHE_URL = (
    "https://wcivf-ballot-cache.s3.eu-west-2.amazonaws.com/ballot_data/"
)
EE_BASE_URL = "https://elections.democracyclub.org.uk/api/"
RECALL_PETITION_ENABLED = True

DEBUG = bool(int(os.environ.get("DEBUG", "0")))
API_PLANS = {
    "hobbyists": ApiPlan(label="Hobbyists", request_per_day=1_000),
    "standard": ApiPlan(label="Standard", request_per_day=10_000),
    "enterprise": ApiPlan(label="Enterprise", request_per_day=0),
}
