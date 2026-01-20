import os
from pathlib import Path

from polars import DataFrame
from static_data_helper import AddressModel, FileNotFoundError, StaticDataHelper

from common.conf import settings

from .models import (
    BasePetitionResponse,
    SigningStationModel,
)

petition_info = {
    # "BPL": BaseRecallPetition(
    #     name="Blackpool South recall petition",
    #     signing_start="2024-03-12",
    #     signing_end="2023-04-22",
    # ),
}


class RecallPetitionApiClient(StaticDataHelper):
    def __init__(self, *args, council_id, **kwargs):
        self.council_id = council_id
        super().__init__(*args, **kwargs)

    def get_postcode_query_expression(self):
        return f"""select * from S3Object s where s.postcode_ns='{self.postcode.without_space}'"""

    def get_bucket_name(self):
        dc_env = os.environ.get("DC_ENVIRONMENT", "development")
        return f"recall-petitions.data.{dc_env}"

    def get_petition_info(self):
        return petition_info[self.council_id]

    def is_split(self, data) -> bool:
        if data.is_empty():
            return False
        return (
            data.group_by(
                "has_recall_petition",
                "station_council_id",
            )
            .len()
            .height
            > 1
        )

    def query_to_dict(self, data: DataFrame):
        if data.is_empty():
            return None
        resp = BasePetitionResponse()
        if self.is_split(data):
            resp.address_picker = True
            resp.addresses = [
                AddressModel.from_row(row, self.request)
                for row in data.to_dicts()
            ]
        else:
            resp.parl_recall_petition = self.get_petition_info()
            row = data[0]
            signing_station = SigningStationModel.from_row(row)
            resp.parl_recall_petition.signing_station = signing_station
        return resp.as_dict()

    def get_file_path(self):
        DATA_BASE_PATH = Path(settings.RECALL_DATA_KEY_PREFIX)
        return DATA_BASE_PATH / self.get_shard_key()

    def patch_response(self, resp):
        try:
            return super().patch_response(resp)
        except FileNotFoundError:
            resp["parl_recall_petition"] = None
            return resp
