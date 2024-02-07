import os
from typing import Any, Dict

from common import settings
from parl_boundary_changes.models import (
    BaseParlBoundariesResponse,
    BaseParlBoundaryChange,
)
from s3_select_helper import AddressModel, S3SelectPostcodeHelper


class ParlBoundaryChangeApiClient(S3SelectPostcodeHelper):
    def get_bucket_name(self) -> str:
        dc_env = os.environ.get("DC_ENVIRONMENT", "development")
        return f"addressbase-lookups.{dc_env}"

    def get_shard_key(self) -> str:
        return f"{settings.PARL_BOUNDARY_DATA_KEY_PREFIX}/{self.postcode.outcode}.parquet"

    def get_input_serialization(self) -> Dict[str, Any]:
        return {"Parquet": {}}

    def get_postcode_query_expression(self) -> str:
        return f"""select * from S3Object s where postcode='{self.postcode.with_space}'"""

    def get_uprn_query_expression(self):
        return f"""select * from S3Object s where uprn={self.uprn}"""

    def query_to_dict(self, query_data):
        old_constituencies = set()
        new_constituencies = set()
        row = None
        for row in query_data:
            old_constituencies.add(
                f"{row['current_constituencies_official_identifier']}-{row['current_constituencies_name']}"
            )
            new_constituencies.add(
                f"{row['new_constituencies_official_identifier']}-{row['new_constituencies_name']}"
            )
        if not row:
            return {"parl_boundary_changes": None}
        old_constituencies = list(old_constituencies)
        new_constituencies = list(new_constituencies)

        resp = BaseParlBoundariesResponse()

        if len(old_constituencies) > 1 or len(new_constituencies) > 1:
            resp.address_picker = True
            resp.addresses = [AddressModel.from_row(row) for row in query_data]
        else:
            resp.parl_boundary_changes = BaseParlBoundaryChange(
                current_constituencies_official_identifier=row[
                    "current_constituencies_official_identifier"
                ],
                current_constituencies_name=row["current_constituencies_name"],
                new_constituencies_official_identifier=row[
                    "new_constituencies_official_identifier"
                ],
                new_constituencies_name=row["new_constituencies_name"],
            )
        return resp.as_dict()

    def postcode_response(self):
        data = self.get_data_for_postcode()
        return self.query_to_dict(data)

    def uprn_response(self):
        data = self.get_data_for_uprn()
        return self.query_to_dict(data)
