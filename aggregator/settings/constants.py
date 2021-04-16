import os

WDIV_BASE_URL = "http://wheredoivote.co.uk/api/beta/"
WDIV_API_KEY = os.environ.get("WDIV_API_KEY", None)
WCIVF_BASE_URL = "http://whocanivotefor.co.uk/api/"
EE_BASE_URL = "https://elections.democracyclub.org.uk/api/"
USER_AGENT = "devs.DC API"
