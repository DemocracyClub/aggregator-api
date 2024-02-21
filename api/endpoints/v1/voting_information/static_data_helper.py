import re
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass

from starlette.requests import Request


class StaticDataHelper(metaclass=ABCMeta):
    """
    Helper function for querying data that's keyed by postcode.
    """

    def __init__(self, request: Request, postcode, uprn=None):
        self.postcode = Postcode(postcode)
        self.uprn = uprn

    @abstractmethod
    def get_shard_key(self):
        ...

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
