from copy import deepcopy
from django.urls import reverse


class StitcherValidationError(Exception):
    pass


class Stitcher:
    def __init__(self, wdiv_resp, wcivf_resp, request):
        self.wdiv_resp = wdiv_resp
        self.wcivf_resp = wcivf_resp
        self.request = request
        self.validate()

    def validate(self):
        # TODO: perform some validation checks here to ensure
        # the wdiv/wcivf responses we've got to work with make sense
        # raise a StitcherValidationError if not
        return True

    def make_address_picker_response(self):
        addresses = []
        for address in self.wdiv_resp["addresses"]:
            addresses.append(
                {
                    "address": address["address"],
                    "postcode": address["postcode"],
                    "slug": address["slug"],
                    "url": self.request.build_absolute_uri(
                        reverse("v1-address", args=(address["slug"],))
                    ),
                }
            )
        response = {"address_picker": True, "addresses": addresses, "results": []}
        return response

    def get_dates(self):
        dates = [ballot["poll_open_date"] for ballot in self.wdiv_resp["ballots"]]
        return sorted(list(set(dates)))

    def get_ballots_for_date(self, date):
        ballots = [
            ballot
            for ballot in self.wdiv_resp["ballots"]
            if ballot["poll_open_date"] == date
        ]
        return ballots

    def get_wcivf_ballot(self, ballot_id):
        for ballot in self.wcivf_resp:
            if ballot["ballot_paper_id"] == ballot_id:
                return ballot
        return None

    @property
    def minimal_wdiv_response(self):
        resp = {}
        fields = (
            "polling_station_known",
            "postcode_location",
            "custom_finder",
            "report_problem_url",
        )
        for field in fields:
            resp[field] = self.wdiv_resp[field]
        resp["council"] = deepcopy(self.wdiv_resp["council"])
        if resp["council"]:
            resp["council"].pop("url", None)
        resp["polling_station"] = deepcopy(self.wdiv_resp["polling_station"])
        if resp["polling_station"]:
            resp["polling_station"]["properties"].pop("urls", None)
            resp["polling_station"]["properties"].pop("council", None)
            resp["polling_station"]["properties"].pop("station_id", None)
        return resp

    def make_result_known_response(self):
        results = []
        dates = self.get_dates()
        for date in dates:
            ballots = self.get_ballots_for_date(date)
            results.append({"date": date, "polling_station": None, "ballots": ballots})
        for date in results:
            for ballot in date["ballots"]:
                wcivf_ballot = self.get_wcivf_ballot(ballot["ballot_paper_id"])
                ballot["election_id"] = wcivf_ballot["election_id"]
                ballot["election_name"] = wcivf_ballot["election_name"]
                ballot["post_name"] = wcivf_ballot["post"]["post_name"]
                ballot["candidates"] = wcivf_ballot["candidates"]
                ballot["wcivf_url"] = wcivf_ballot["absolute_url"]
        if results:
            results[0]["polling_station"] = self.minimal_wdiv_response
        response = {"address_picker": False, "addresses": [], "results": results}
        return response
