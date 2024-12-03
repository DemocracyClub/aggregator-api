import os

import requests


def make_request(url):
    dc_env = os.environ.get("DC_ENVIRONMENT")

    if dc_env == "development" or dc_env == "staging":
        resp = requests.get(
            url,
            timeout=20,
            auth=("dc", "dc"),
        )
    else:
        resp = requests.get(url, timeout=20)

    return resp
