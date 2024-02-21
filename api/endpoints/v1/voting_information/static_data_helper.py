import json
import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass

import boto3
from botocore.exceptions import ClientError
from starlette.requests import Request


class S3SelectPostcodeHelper(metaclass=ABCMeta):
    """
    Helper function for querying data on S3 that's keyed by postcode

    """

    def __init__(self, request: Request, postcode, uprn=None):
        self.postcode = Postcode(postcode)
        self.uprn = uprn
        self.s3_client = get_s3_client()

    @abstractmethod
    def get_shard_key(self):
        ...

    @abstractmethod
    def get_bucket_name(self):
        ...

    @abstractmethod
    def get_input_serialization(self):
        ...

    @abstractmethod
    def get_postcode_query_expression(self):
        ...

    @abstractmethod
    def get_uprn_query_expression(self):
        ...

    def get_data_for_postcode(self):
        """
        Use S3 Select to get all addresses that match the postcode.

        Return a list of dicts, where the dict represents the CSV row in the
        source file.

        """

        shard_key = self.get_shard_key()

        bucket_name = self.get_bucket_name()
        try:
            resp = self.s3_client.select_object_content(
                Bucket=bucket_name,
                Key=shard_key,
                Expression=self.get_postcode_query_expression(),
                ExpressionType="SQL",
                InputSerialization=self.get_input_serialization(),
                OutputSerialization={"JSON": {}},
            )
        except AttributeError:
            # Special case for Moto that doesn't return a ClientError
            return []
        except ClientError as ex:
            if ex.response["Error"]["Code"] == "NoSuchKey":
                # If there's no key for whatever reason, just return quietly
                return []
            raise

        return self._response_to_list(resp)

    def get_data_for_uprn(self):
        """
        Use S3 Select to get the row matching the UPRN.

        Return a list of dicts, where the dict represents the CSV row in the
        source file.

        """
        shard_key = self.get_shard_key()

        bucket_name = self.get_bucket_name()
        resp = self.s3_client.select_object_content(
            Bucket=bucket_name,
            Key=shard_key,
            Expression=self.get_uprn_query_expression(),
            ExpressionType="SQL",
            InputSerialization=self.get_input_serialization(),
            OutputSerialization={"JSON": {}},
        )
        return self._response_to_list(resp)

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

        resp.update(new_response_data)
        return resp


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

    @classmethod
    def from_row(cls, row):
        return cls(
            slug=row["uprn"],
            address=row["address"],
            postcode=row["postcode"],
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
