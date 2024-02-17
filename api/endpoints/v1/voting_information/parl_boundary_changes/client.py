from pathlib import Path
from typing import Optional

import polars
from parl_boundary_changes.models import (
    BaseParlBoundariesResponse,
    BaseParlBoundaryChange,
)
from polars import DataFrame
from s3_select_helper import AddressModel, Postcode
from starlette.requests import Request

DATA_BASE_PATH = Path("/home/symroe/Data/devs.dc/parl-boundaries")


class ParlBoundaryChangeApiClient:
    def __init__(self, request: Request, postcode, uprn: Optional[int] = None):
        self.postcode = Postcode(postcode)
        self.uprn = uprn

    def get_filename(self):
        filename = f"{self.postcode.outcode}.parquet"
        return DATA_BASE_PATH / filename

    def postcode_response(self):
        data = self.get_data_for_postcode()
        return self.query_to_dict(data)

    def uprn_response(self):
        data = self.get_data_for_uprn()
        return self.query_to_dict(data)

    def get_data_for_postcode(self):
        return polars.read_parquet(self.get_filename()).filter(
            (polars.col("postcode") == self.postcode.with_space)
        )

    def get_data_for_uprn(self):
        return self.get_data_for_postcode().filter(
            (polars.col("uprn") == self.uprn)
        )

    def is_split(self, data) -> bool:
        return (
            data.group_by(
                "current_constituencies_official_identifier",
                "new_constituencies_official_identifier",
            )
            .len()
            .height
            > 1
        )

    def query_to_dict(self, data: DataFrame):
        resp = BaseParlBoundariesResponse()
        if self.is_split(data):
            resp.address_picker = True
            resp.addresses = [AddressModel.from_row(row) for row in data]
        else:
            row = data[0]
            resp.parl_boundary_changes = BaseParlBoundaryChange.from_row(row)
        print(resp.as_dict())
        return resp.as_dict()
