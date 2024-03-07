from pathlib import Path
from typing import IO

import polars
from botocore.exceptions import ClientError
from common.conf import settings
from parl_boundary_changes.models import (
    BaseParlBoundariesResponse,
    BaseParlBoundaryChange,
)
from polars import DataFrame
from static_data_helper import AddressModel, StaticDataHelper


class FileNotFoundError(ValueError):
    ...


class ParlBoundaryChangeApiClient(StaticDataHelper):
    def get_bucket_name(self):
        return settings.PARL_BOUNDARY_DATA_BUCKET_NAME

    def get_shard_key(self):
        return f"{self.postcode.outcode}.parquet"

    def get_file_path(self):
        DATA_BASE_PATH = Path(settings.PARL_BOUNDARY_DATA_KEY_PREFIX)
        return DATA_BASE_PATH / self.get_shard_key()

    def get_filename_or_file(self) -> Path | IO:
        """
        If we use S3 then we want to use boto3 to download the file
        and return the bytes.

        If we're not using S3, assume the file we're reading is local.

        The Polars interface allows passing in either a IO object (e.g a file) or a path.

        We can take advantage of this here.

        :return:
        """
        if settings.S3_CLIENT_ENABLED:
            try:
                response = settings.S3_CLIENT.get_object(
                    Bucket=self.get_bucket_name(), Key=str(self.get_file_path())
                )
            except ClientError as ex:
                if ex.response["Error"]["Code"] == "NoSuchKey":
                    # If there's no key for whatever reason raise
                    raise FileNotFoundError()
                # Raie any other boto3 errors
                raise
            return response["Body"].read()

        return self.get_local_file_name()

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

    def get_local_file_name(self):
        if not settings.LOCAL_DATA_PATH:
            raise ValueError(
                "LOCAL_DATA_PATH isn't set. Export `LOCAL_STATIC_DATA_PATH`"
            )
        local_file_path = Path(settings.LOCAL_DATA_PATH) / self.get_file_path()
        if not local_file_path.exists():
            print(f"WARNING: local data doesn't exist at {local_file_path}")
            raise FileNotFoundError()
        return local_file_path
