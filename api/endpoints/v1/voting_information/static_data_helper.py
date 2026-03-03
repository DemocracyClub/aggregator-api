import logging
import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, List, Optional

import polars
from botocore.exceptions import ClientError
from sentry_sdk import get_current_scope, set_context
from starlette.requests import Request

from common.conf import settings

logger = logging.getLogger(__name__)


class StaticDataHelper(metaclass=ABCMeta):
    """
    Helper function for querying data that's keyed by postcode.
    """

    def __init__(self, request: Request, postcode, uprn=None):
        self.postcode = Postcode(postcode)
        self.uprn = uprn
        self.request = request

    def get_shard_key(self):
        return f"{self.postcode.outcode}.parquet"

    @abstractmethod
    def get_file_path(self):
        ...

    def get_local_file_name(self):
        if not settings.LOCAL_DATA_PATH:
            raise ValueError(
                "LOCAL_DATA_PATH isn't set. Export `LOCAL_STATIC_DATA_PATH`"
            )
        local_file_path = Path(settings.LOCAL_DATA_PATH) / self.get_file_path()
        if not local_file_path.exists():
            logger.warning(
                f"WARNING: Local data path {local_file_path} doesn't exist"
            )
            raise FileNotFoundError()
        return local_file_path

    @abstractmethod
    def get_bucket_name(self):
        ...

    def get_data_for_postcode(self):
        df = polars.read_parquet(self.get_filename_or_file())
        if df.height == 0:
            # empty parquet file, return early
            return df

        postcode_df = df.filter(
            (polars.col("postcode") == self.postcode.with_space)
        )

        if postcode_df.height == 0:
            # ERROR
            # In theory this shouldn't happen
            # but if our 2 copies of AddressBase (local DB and parquet files)
            # are out of sync this will totally happen at some point
            message = (
                f"Postcode {self.postcode.with_space} did not exist in outcode Parquet file"
            )
            scope = get_current_scope()
            scope.fingerprint = ["parquet:postcode_not_in_parquet_file"]
            logging.error(message)

            # Still return the empty df
            return postcode_df

        self.data_quality_check(postcode_df)
        return postcode_df

    def get_data_for_uprn(self):
        postcode_df = self.get_data_for_postcode()

        if postcode_df.height == 0:
            # We've already raised an error in get_data_for_postcode
            # so just return
            return postcode_df


        uprn_df = postcode_df.filter((polars.col("uprn") == str(self.uprn)))

        if uprn_df.height == 0:
            # ERROR
            # In theory this shouldn't happen
            # but if our 2 copies of AddressBase (local DB and parquet files)
            # are out of sync this will totally happen at some point
            message = (
                f"UPRN {str(self.uprn)} did not exist in outcode Parquet file for {self.postcode.with_space}"
            )
            scope = get_current_scope()
            scope.fingerprint = ["parquet:uprn_not_in_parquet_file"]
            logging.error(message)

            # Still return the empty df
            return postcode_df

        return uprn_df

    def postcode_response(self):
        data = self.get_data_for_postcode()
        return self.query_to_dict(data)

    def uprn_response(self):
        data = self.get_data_for_uprn()
        return self.query_to_dict(data)

    def data_quality_check(self, postcode_df):
        if postcode_df.select("uprn").unique().height != postcode_df.height:
            duplicate_uprns = (
                postcode_df.group_by("uprn")
                .len()
                .filter(polars.col("len") > 1)["uprn"]
                .to_list()
            )
            raise DuplicateUPRNError(
                postcode=self.postcode.with_space, uprns=duplicate_uprns
            )
        if postcode_df.select("addressbase_source").unique().height > 1:
            sources = (
                postcode_df.select("addressbase_source")
                .unique()["addressbase_source"]
                .to_list()
            )
            raise MultipleAddressbaseSourceError(
                postcode=self.postcode.with_space, sources=sources
            )

    @abstractmethod
    def query_to_dict(self, query_data):
        pass

    def patch_response(self, resp):
        if self.uprn:
            new_response_data = self.uprn_response()
        else:
            new_response_data = self.postcode_response()

        if not new_response_data:
            return resp
        if new_response_data and new_response_data["address_picker"]:
            new_response_data["postcode_location"] = resp["postcode_location"]
            return new_response_data
        new_response_data["electoral_services"] = resp.get("electoral_services")
        new_response_data["registration"] = resp.get("registration")
        resp.update(new_response_data)
        return resp

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
            key = str(self.get_file_path())
            bucket = self.get_bucket_name()
            try:
                response = settings.S3_CLIENT.get_object(Bucket=bucket, Key=key)
            except ClientError as ex:
                if ex.response["Error"]["Code"] == "NoSuchKey":
                    set_context(
                        "Missing File", {"s3_key": key, "bucket": bucket}
                    )
                    logger.error(f"S3 key {key} not found in {bucket}")
                    raise FileNotFoundError()
                # Raise any other boto3 errors
                raise
            return response["Body"].read()

        return self.get_local_file_name()


class BaseDictDataclass:
    def as_dict(self):
        for key, value in self.__dict__.items():
            if hasattr(value, "as_dict"):
                setattr(self, key, value.as_dict())
            if isinstance(value, list):
                _new = []
                for kk in value:
                    if hasattr(kk, "as_dict"):
                        _new.append(kk.as_dict())
                    else:
                        _new.append(kk)
                setattr(self, key, _new)
        return self.__dict__


@dataclass(eq=True, unsafe_hash=True)
class AddressModel(BaseDictDataclass):
    address: str
    postcode: str
    slug: str
    url: str

    @classmethod
    def from_row(cls, row, request: Request):
        url = str(request.url_for("address", uprn=row["uprn"]))
        return cls(
            slug=row["uprn"],
            address=row["address"],
            postcode=row["postcode"],
            url=url,
        )


class Postcode:
    def __init__(self, postcode: str):
        self.postcode = re.sub("[^A-Z0-9]", "", str(postcode).upper())

    @property
    def with_space(self):
        return self.postcode[:-3] + " " + self.postcode[-3:]

    @property
    def without_space(self):
        return self.postcode

    @property
    def outcode(self):
        return self.with_space.split()[0]

    def __str__(self):
        return self.without_space


class FileNotFoundError(ValueError):
    ...


class DuplicateUPRNError(ValueError):
    def __init__(self, postcode, uprns):
        message = (
            f"Duplicate UPRNs found for postcode {postcode}: {sorted(uprns)}"
        )
        super().__init__(message)


class MultipleAddressbaseSourceError(ValueError):
    def __init__(self, postcode, sources):
        message = f"Multiple addressbase sources found for postcode {postcode}: {sorted(sources)}"
        super().__init__(message)


@dataclass
class BaseResponse(BaseDictDataclass):
    addresses: Optional[List[AddressModel]] = field(default_factory=list)
    address_picker: bool = field(default=False)
    electoral_services: bool = None
    registration: bool = None
