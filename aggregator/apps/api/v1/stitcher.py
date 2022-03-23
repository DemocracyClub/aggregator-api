import re
from copy import deepcopy
from django.urls import reverse
from sentry_sdk import capture_message


def ballot_charisma(ballot, sort_keys):
    charisma_map = {
        "ref": {"default": 100},
        "parl": {"default": 90},
        "europarl": {"default": 80},
        "mayor": {"default": 70, "local-authority": 65},
        "nia": {"default": 60},
        "gla": {"default": 60, "a": 55},
        "naw": {"default": 60, "r": 55},
        "senedd": {"default": 60, "r": 55},
        "sp": {"default": 60, "r": 55},
        "pcc": {"default": 50},
        "local": {"default": 40},
    }
    modifier = 0
    ballot_paper_id = ballot["ballot_paper_id"]

    # Look up the dict of possible weights for this election type
    weights = charisma_map.get(ballot_paper_id.split(".")[0], 30)

    # Extract the organisation type from the sort keys
    organisation_type = sort_keys.get(ballot_paper_id)

    default_weight_for_election_type = weights.get("default")
    base_charisma = weights.get(organisation_type, default_weight_for_election_type)

    # Look up `r` and `a` subtypes
    subtype = re.match(r"^[^.]+\.([ar])\.", ballot_paper_id)
    if subtype:
        base_charisma = weights.get(subtype.group(1), base_charisma)

    # by-elections are slightly less charismatic than scheduled elections
    if ".by." in ballot_paper_id:
        modifier += 1

    return base_charisma - modifier


def sort_ballots(dates, sort_keys):
    for date in dates:
        date["ballots"] = sorted(
            date["ballots"], key=lambda k: ballot_charisma(k, sort_keys), reverse=True
        )
    return dates


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
        self.wcivf_ballots = self.make_wcivf_ballots()
        self.ballot_sort_keys = {}
        self.request = request
        self.validate()

    def validate(self):
        for ballot in self.wdiv_resp["ballots"]:
            if ballot["ballot_paper_id"] not in self.wcivf_ballots:
                message = f'Could not find expected ballot {ballot["ballot_paper_id"]}'
                # Log the mismatched ballots to sentry, but don't raise an error
                capture_message(message)
                return False

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
        if not council:
            return None
        details = council.get("registration_contacts", None)
        if details:
            try:
                details["phone"] = details.get("phone_numbers", [])[0]
            except IndexError:
                details["phone"] = ""
        else:
            details = self.get_electoral_services()
        return details

    def make_wcivf_ballots(self):
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
                    "slug": address["uprn"],
                    "url": self.request.build_absolute_uri(
                        reverse("api:v1:address", args=(address["uprn"],))
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
        return ballots

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
                    "advance_voting_station": None,
                    "notifications": nm.notifications,
                    "ballots": ballots,
                }
            )

        for date in results:
            for i, ballot in enumerate(date["ballots"]):
                wcivf_ballot = self.wcivf_ballots.get(ballot["ballot_paper_id"])
                if not wcivf_ballot:
                    del date["ballots"][i]
                    continue

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
                ballot["hustings"] = wcivf_ballot.get("hustings", None)

                # We only sort by organisation_type at the moment, but we
                # could add more values here to sort by more fields
                self.ballot_sort_keys[ballot["ballot_paper_id"]] = wcivf_ballot[
                    "organisation_type"
                ]
        if results:
            results[0]["polling_station"] = self.minimal_wdiv_response
            results[0]["advance_voting_station"] = self.wdiv_resp.get(
                "advance_voting_station", None
            )
        response = {
            "address_picker": False,
            "addresses": [],
            "dates": sort_ballots(results, self.ballot_sort_keys),
            "electoral_services": self.get_electoral_services(),
            "registration": self.get_registration_contacts(),
            "postcode_location": self.wdiv_resp["postcode_location"],
        }
        return response
