import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, List, Optional

from botocore.exceptions import ClientError
from common.conf import settings
from starlette.requests import Request


class StaticDataHelper(metaclass=ABCMeta):
    """
    Helper function for querying data that's keyed by postcode.
    """

    def __init__(self, request: Request, postcode, uprn=None):
        self.postcode = Postcode(postcode)
        self.uprn = uprn
        self.request = request

    @abstractmethod
    def get_shard_key(self):
        ...

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
            print(f"WARNING: local data doesn't exist at {local_file_path}")
            raise FileNotFoundError()
        return local_file_path

    @abstractmethod
    def get_bucket_name(self):
        ...

    def get_data_for_postcode(self):
        ...

    def get_data_for_uprn(self):
        ...

    @abstractmethod
    def postcode_response(self):
        pass

    @abstractmethod
    def uprn_response(self):
        pass

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


@dataclass
class BaseResponse(BaseDictDataclass):
    addresses: Optional[List[AddressModel]] = field(default_factory=list)
    address_picker: bool = field(default=False)
    electoral_services: bool = None
    registration: bool = None
