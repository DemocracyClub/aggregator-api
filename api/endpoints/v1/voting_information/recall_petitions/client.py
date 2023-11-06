import json
import os
import re

import boto3
from starlette.requests import Request

from .models import (
    AddressModel,
    BaseRecallPetition,
    BaseResponse,
    SigningStationModel,
)

client = boto3.client("s3")

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


def clean_postcode(postcode):
    postcode = postcode.upper()
    return re.sub(r"\s", "", postcode)


class RecallPetitionApiClient:
    def __init__(self, request: Request, council_id: str):
        self.request = request
        self.council_id = council_id

    def _response_to_list(self, response):
        data = []
        for event in response["Payload"]:
            if "Records" in event:
                records = event["Records"]["Payload"].decode().split("\n")
                for record in records:
                    if not record:
                        continue
                    data.append(json.loads(record))
        return data

    def get_petition_info(self):
        return petition_info[self.council_id]

    def get_data_for_postcode(self, postcode):
        """
        Use S3 Select to get all addresses that match the postcode.

        Return a list of dicts, where the dict represents the CSV row in the
        source file.

        """

        postcode = clean_postcode(postcode)
        shard_key = self.get_petition_info()["data_file"]
        dc_env = os.environ.get("DC_ENVIRONMENT", "development")
        bucket_name = f"recall-petitions.data.{dc_env}"
        resp = client.select_object_content(
            Bucket=bucket_name,
            Key=shard_key,
            Expression=f"""select * from S3Object s where s.postcode_ns='{postcode}'""",
            ExpressionType="SQL",
            InputSerialization={
                "CSV": {
                    "FileHeaderInfo": "Use",
                    "AllowQuotedRecordDelimiter": True,
                }
            },
            OutputSerialization={"JSON": {}},
        )
        return self._response_to_list(resp)

    def get_data_for_uprn(self, uprn):
        """
        Use S3 Select to get the row matching the UPRN.

        Return a list of dicts, where the dict represents the CSV row in the
        source file.

        """
        shard_key = self.get_petition_info()["data_file"]
        dc_env = os.environ.get("DC_ENVIRONMENT", "development")
        bucket_name = f"recall-petitions.data.{dc_env}"
        resp = client.select_object_content(
            Bucket=bucket_name,
            Key=shard_key,
            Expression=f"""select * from S3Object s where s.uprn='{uprn}'""",
            ExpressionType="SQL",
            InputSerialization={
                "CSV": {
                    "FileHeaderInfo": "Use",
                    "AllowQuotedRecordDelimiter": True,
                }
            },
            OutputSerialization={"JSON": {}},
        )
        return self._response_to_list(resp)

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

    def postcode_response(self, postcode):
        data = self.get_data_for_postcode(postcode)
        return self.query_to_dict(data)

    def uprn_response(self, uprn):
        data = self.get_data_for_uprn(uprn)
        return self.query_to_dict(data)

    def patch_response(self, resp):
        if postcode := self.request.path_params.get("postcode"):
            petition = self.postcode_response(postcode)
        else:
            petition = self.uprn_response(self.request.path_params["uprn"])
        resp.update(petition)
        return resp
