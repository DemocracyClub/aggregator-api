import polars
from common.conf import settings
from parl_boundary_changes.models import (
    BaseParlBoundariesResponse,
    BaseParlBoundaryChange,
)
from polars import DataFrame
from static_data_helper import AddressModel, FileNotFoundError, StaticDataHelper


class ParlBoundaryChangeApiClient(StaticDataHelper):
    def get_bucket_name(self):
        return settings.PARL_BOUNDARY_DATA_BUCKET_NAME

    def get_shard_key(self):
        return f"{self.postcode.outcode}.parquet"

    def postcode_response(self):
        data = self.get_data_for_postcode()
        return self.query_to_dict(data)

    def uprn_response(self):
        data = self.get_data_for_uprn()
        return self.query_to_dict(data)

    def get_data_for_postcode(self):
        return polars.read_parquet(self.get_filename_or_file()).filter(
            (polars.col("postcode") == self.postcode.with_space)
        )

    def get_data_for_uprn(self):
        return self.get_data_for_postcode().filter(
            (polars.col("uprn") == int(self.uprn))
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
            resp.addresses = [
                AddressModel.from_row(row, self.request)
                for row in data.to_dicts()
            ]
        else:
            row = data[0]
            resp.parl_boundary_changes = BaseParlBoundaryChange.from_row(row)
        return resp.as_dict()

    def patch_response(self, resp):
        try:
            if self.uprn:
                new_response_data = self.uprn_response()
            else:
                new_response_data = self.postcode_response()
        except FileNotFoundError:
            # For some reason we can't load the data.
            # Don't break the site in this case!
            resp["parl_boundary_changes"] = None
            new_response_data = resp
        resp.update(new_response_data)
        return resp
