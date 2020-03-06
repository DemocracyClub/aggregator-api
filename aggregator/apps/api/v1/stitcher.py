from copy import deepcopy
from django.urls import reverse


def ballot_charisma(ballot):
    charisma_map = {
        "ref": 100,
        "parl": 90,
        "europarl": 80,
        "mayor": 70,
        "naw": 60,
        "sp": 60,
        "nia": 60,
        "gla": 60,
        "pcc": 50,
        "local": 40,
    }

    base_charisma = charisma_map[ballot["ballot_paper_id"].split(".")[0]]
    # by-elections are slightly less charismatic than scheduled elections
    by_election_modifier = int(".by." in ballot["ballot_paper_id"])

    return base_charisma - by_election_modifier


def sort_ballots(ballots):
    return sorted(ballots, key=lambda k: ballot_charisma(k), reverse=True)


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
        self.wcivf_by_ballot = self.make_wcivf_by_ballot()
        self.request = request
        self.validate()

    def validate(self):
        for ballot in self.wdiv_resp["ballots"]:
            if ballot["ballot_paper_id"] not in self.wcivf_by_ballot:
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
            council.pop("electoral_services_contacts", None)
            council.pop("registration_contacts", None)
        return council

    def get_registration_contacts(self):
        council = deepcopy(self.wdiv_resp["council"])
        return council.get("registration_contacts", self.get_electoral_services())

    def make_wcivf_by_ballot(self):
        """
        Iterate over the WCIVF response once to create a dict keyed by
        ballot paper ID
        """
        by_ballot = {}
        for ballot in self.wcivf_resp:
            by_ballot[ballot["ballot_paper_id"]] = ballot
        return by_ballot

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
            "registration": self.get_registration_contacts(),
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
        return sort_ballots(ballots)

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
                wcivf_ballot = self.wcivf_by_ballot[ballot["ballot_paper_id"]]

                ballot["ballot_url"] = self.request.build_absolute_uri(
                    reverse("api:v1:elections_get", args=(ballot["ballot_paper_id"],))
                )
                ballot["election_id"] = wcivf_ballot["election_id"]
                ballot["election_name"] = wcivf_ballot["election_name"]
                ballot["post_name"] = wcivf_ballot["post"]["post_name"]
                ballot["candidates_verified"] = wcivf_ballot["ballot_locked"]
                ballot["candidates"] = wcivf_ballot["candidates"]
                ballot["wcivf_url"] = wcivf_ballot["absolute_url"]
                ballot["voting_system"] = wcivf_ballot["voting_system"]
                ballot["seats_contested"] = wcivf_ballot["seats_contested"]
        if results:
            results[0]["polling_station"] = self.minimal_wdiv_response
        response = {
            "address_picker": False,
            "addresses": [],
            "dates": results,
            "electoral_services": self.get_electoral_services(),
            "registration": self.get_registration_contacts(),
            "postcode_location": self.wdiv_resp["postcode_location"],
        }
        return response
