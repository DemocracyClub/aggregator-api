import os

USER_AGENT = os.environ.get("API_USER_AGENT", "devs.DC API")
WDIV_API_KEY = os.environ.get("WDIV_API_KEY", None)

WDIV_BASE_URL = "https://wheredoivote.co.uk/api/beta/"
WCIVF_BASE_URL = "https://whocanivotefor.co.uk/api/"
WCIVF_BALLOT_CACHE_URL = (
    "https://wcivf-ballot-cache.s3.eu-west-2.amazonaws.com/ballot_data/"
)
EE_BASE_URL = "https://elections.democracyclub.org.uk/api/"
RECALL_PETITION_BASE_URL = (
    "https://klbyvve95g.execute-api.eu-west-2.amazonaws.com/prod/"
)

DEBUG = bool(int(os.environ.get("DEBUG", "0")))
