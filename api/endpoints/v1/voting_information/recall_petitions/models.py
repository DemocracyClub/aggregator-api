from dataclasses import dataclass, field
from typing import List, Optional

from s3_select_helper import AddressModel, BaseDictDataclass


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
