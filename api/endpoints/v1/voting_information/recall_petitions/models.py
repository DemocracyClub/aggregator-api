from dataclasses import dataclass, field
from typing import List, Optional


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
class SigningStationModel(BaseDictDataclass):
    station_id: str
    address: str
    postcode: str

    @classmethod
    def from_row(cls, row):
        return cls(
            station_id=row["station_council_id"],
            address=row["station_address"],
            postcode=row["station_postcode"],
        )


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


@dataclass
class BaseRecallPetition(BaseDictDataclass):
    name: str = field(default=None)
    signing_start: str = field(default=None)
    signing_end: str = field(default=None)
    signing_station: Optional[SigningStationModel] = field(default=None)


@dataclass
class BaseResponse(BaseDictDataclass):
    parl_recall_petition: Optional[BaseRecallPetition] = field(default=None)
    addresses: Optional[List[AddressModel]] = field(default_factory=list)
    address_picker: bool = field(default=False)
