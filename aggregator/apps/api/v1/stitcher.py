from copy import deepcopy
from django.urls import reverse


class StitcherValidationError(Exception):
    pass


class NotificationsMaker:
    def __init__(self, ballots):
        self.ballots = ballots
        self.cancelled_ballots = self.get_cancelled_ballots()

    def get_cancelled_ballots(self):
        return [b for b in self.ballots if b["cancelled"]]

    def get_metadata_by_key(self, key):
        for b in self.ballots:
            if b["metadata"] and key in b["metadata"]:
                return b["metadata"][key]
        return None

    @property
    def all_ballots_cancelled(self):
        return len(self.cancelled_ballots) > 0 and len(self.ballots) == len(
            self.cancelled_ballots
        )

    @property
    def notifications(self):
        if self.all_ballots_cancelled:
            notification = self.get_metadata_by_key("cancelled_election")
            notification["type"] = "cancelled_election"
            return [notification]

        notification = self.get_metadata_by_key(
            "2019-05-02-id-pilot"
        ) or self.get_metadata_by_key("ni-voter-id")
        if notification:
            notification["type"] = "voter_id"
            return [notification]

        return []


class Stitcher:
    def __init__(self, wdiv_resp, wcivf_resp, request):
        self.wdiv_resp = wdiv_resp
        self.wcivf_resp = wcivf_resp
        self.request = request
        self.validate()

    def validate(self):
        for ballot in self.wdiv_resp["ballots"]:
            if not self.get_wcivf_ballot(ballot["ballot_paper_id"]):
                raise StitcherValidationError(
                    f'Could not find expected ballot {ballot["ballot_paper_id"]}'
                )

        # TODO: define a schema and validate against it here to ensure
        # the wdiv/wcivf responses we've got to work with make sense

        return True

    def get_electoral_services(self):
        council = deepcopy(self.wdiv_resp["council"])
        if council:
            council.pop("url", None)
        return council

    def make_address_picker_response(self):
        addresses = []
        for address in self.wdiv_resp["addresses"]:
            addresses.append(
                {
                    "address": address["address"],
                    "postcode": address["postcode"],
                    "slug": address["slug"],
                    "url": self.request.build_absolute_uri(
                        reverse("api:v1:address", args=(address["slug"],))
                    ),
                }
            )
        response = {
            "address_picker": True,
            "addresses": addresses,
            "dates": [],
            "electoral_services": self.get_electoral_services(),
            "postcode_location": self.wdiv_resp["postcode_location"],
        }
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

        # TODO: define a full hierarchy of election interesting-ness
        return sorted(ballots, key=lambda k: int(".by." in k["ballot_paper_id"]))

    def get_wcivf_ballot(self, ballot_id):
        for ballot in self.wcivf_resp:
            if ballot["ballot_paper_id"] == ballot_id:
                return ballot
        return None

    @property
    def minimal_wdiv_response(self):
        resp = {}
        fields = ("polling_station_known", "custom_finder", "report_problem_url")
        for field in fields:
            resp[field] = self.wdiv_resp[field]
        resp["station"] = deepcopy(self.wdiv_resp["polling_station"])
        if resp["station"]:
            resp["station"]["properties"].pop("urls", None)
            resp["station"]["properties"].pop("council", None)
            resp["station"]["properties"].pop("station_id", None)
        return resp

    def make_result_known_response(self):
        results = []
        dates = self.get_dates()
        for date in dates:
            ballots = self.get_ballots_for_date(date)
            nm = NotificationsMaker(ballots)
            results.append(
                {
                    "date": date,
                    "polling_station": {
                        "polling_station_known": False,
                        "custom_finder": None,
                        "report_problem_url": None,
                        "station": None,
                    },
                    "notifications": nm.notifications,
                    "ballots": ballots,
                }
            )
        for date in results:
            for ballot in date["ballots"]:
                wcivf_ballot = self.get_wcivf_ballot(ballot["ballot_paper_id"])

                ballot["ballot_url"] = self.request.build_absolute_uri(
                    reverse("api:v1:elections_get", args=(ballot["ballot_paper_id"],))
                )
                ballot["election_id"] = wcivf_ballot["election_id"]
                ballot["election_name"] = wcivf_ballot["election_name"]
                ballot["post_name"] = wcivf_ballot["post"]["post_name"]
                ballot["candidates_verified"] = wcivf_ballot["ballot_locked"]
                ballot["candidates"] = wcivf_ballot["candidates"]
                ballot["wcivf_url"] = wcivf_ballot["absolute_url"]
        if results:
            results[0]["polling_station"] = self.minimal_wdiv_response
        response = {
            "address_picker": False,
            "addresses": [],
            "dates": results,
            "electoral_services": self.get_electoral_services(),
            "postcode_location": self.wdiv_resp["postcode_location"],
        }
        return response
