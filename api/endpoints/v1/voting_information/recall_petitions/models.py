from dataclasses import dataclass, field
from typing import Optional

from polars import DataFrame
from static_data_helper import BaseDictDataclass, BaseResponse


@dataclass(eq=True, unsafe_hash=True)
class SigningStationModel(BaseDictDataclass):
    station_id: str
    address: str
    postcode: str

    @classmethod
    def from_row(cls, row: DataFrame):
        row_dict = row.to_dict(as_series=False)

        kwargs = {
            "station_id": row_dict["station_council_id"][0],
            "address": row_dict["station_address"][0],
            "postcode": row_dict["station_postcode"][0],
        }
        return cls(**kwargs)


@dataclass
class BaseRecallPetition(BaseDictDataclass):
    name: str = field(default=None)
    signing_start: str = field(default=None)
    signing_end: str = field(default=None)
    signing_station: Optional[SigningStationModel] = field(default=None)

    @classmethod
    def from_row(cls, row: DataFrame, petition_info):
        row_dict = row.to_dict(as_series=False)
        fields = [
            "polling_place_name",
            "station_address",
        ]
        kwargs = {
            "signing_start": petition_info["signing_start"],
            "signing_end": petition_info["signing_end"],
            "signing_station": SigningStationModel.from_row(row),
        }
        for attr in fields:
            kwargs[attr] = row_dict[attr][0]
        return cls(**kwargs)


@dataclass
class BasePetitionResponse(BaseResponse):
    parl_recall_petition: Optional[BaseRecallPetition] = field(default=None)
