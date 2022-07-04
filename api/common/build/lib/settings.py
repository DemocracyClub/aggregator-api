import os

USER_AGENT = os.environ.get("API_USER_AGENT", "devs.DC API")
WDIV_API_KEY = os.environ.get("WDIV_API_KEY", None)

WDIV_BASE_URL = "http://wheredoivote.co.uk/api/beta/"
WCIVF_BASE_URL = "http://whocanivotefor.co.uk/api/"
EE_BASE_URL = "https://elections.democracyclub.org.uk/api/"
