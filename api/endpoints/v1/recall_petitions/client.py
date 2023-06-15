import httpx
from common import settings
from common.url_resolver import build_absolute_url


class RecallPetitionApiClient:
    postcode_base_url = f"{settings.RECALL_PETITION_BASE_URL}postcode"
    address_base_url = f"{settings.RECALL_PETITION_BASE_URL}address"

    def __init__(self, request):
        self.request = request
        self.sandbox = False

    def get_json(self, url):
        recall_resp = httpx.get(url).json()
        addresses = []
        if recall_resp["address_picker"]:
            for address in recall_resp["addresses"]:
                address["url"] = build_absolute_url(
                    self.request.base_url,
                    "recall_petitions_address",
                    uprn=address["slug"],
                    sandbox=self.sandbox,
                )
                addresses.append(address)
        recall_resp["addresses"] = addresses
        return recall_resp

    def get_data_for_postcode(self, postcode):
        postcode_url = f"{self.postcode_base_url}/{postcode}/"
        return self.get_json(postcode_url)

    def get_data_for_address(self, uprn):
        address_url = f"{self.address_base_url}/{uprn}/"
        return self.get_json(address_url)
