import os

from static_data_helper import AddressModel, StaticDataHelper

from .models import (
    BaseRecallPetition,
    BaseResponse,
    SigningStationModel,
)

petition_info = {
    "NNT": {
        "data_file": "wellingborough-recall-petition.csv",
        "petition": BaseRecallPetition(
            name="Wellingborough recall petition",
            signing_start="2023-11-08",
            signing_end="2023-12-19",
        ),
        "constituency_name": "Wellingborough",
    },
    "SLK": {
        "data_file": "rutherglen-west-hamilton.csv",
        "petition": BaseRecallPetition(
            name="Rutherglen and Hamilton West recall petition",
            signing_start="2023-06-20",
            signing_end="2023-07-31",
        ),
        "constituency_name": "Rutherglen and Hamilton West",
    },
}


class RecallPetitionApiClient(StaticDataHelper):
    def __init__(self, *args, council_id, **kwargs):
        self.council_id = council_id
        super().__init__(*args, **kwargs)

    def get_postcode_query_expression(self):
        return f"""select * from S3Object s where s.postcode_ns='{self.postcode.without_space}'"""

    def get_shard_key(self):
        return self.get_petition_info()["data_file"]

    def get_bucket_name(self):
        dc_env = os.environ.get("DC_ENVIRONMENT", "development")
        return f"recall-petitions.data.{dc_env}"

    def get_input_serialization(self):
        return {
            "CSV": {
                "FileHeaderInfo": "Use",
                "AllowQuotedRecordDelimiter": True,
            }
        }

    def get_petition_info(self):
        return petition_info[self.council_id]

    def query_to_dict(self, query_data):
        signing_stations = set()
        constituencies = set()
        for row in query_data:
            constituencies.add(row["organisationdivision__name"])
            station = SigningStationModel.from_row(row)
            signing_stations.add(station)
        signing_stations = list(signing_stations)

        if not signing_stations:
            return {}

        # If none of the addresses are in the constituency, then don't show anything about the petition
        if self.get_petition_info()["constituency_name"] not in constituencies:
            return {}

        resp = BaseResponse()

        signing_station = None

        if len(signing_stations) > 1:
            resp.address_picker = True
            resp.addresses = [AddressModel.from_row(row) for row in query_data]
        else:
            signing_station = signing_stations[0]

        if signing_station:
            resp.parl_recall_petition = self.get_petition_info()["petition"]
            if signing_station.station_id:
                resp.parl_recall_petition.signing_station = signing_station

        return resp.as_dict()

    def postcode_response(self):
        data = self.get_data_for_postcode()
        return self.query_to_dict(data)

    def uprn_response(self):
        data = self.get_data_for_uprn()
        return self.query_to_dict(data)
