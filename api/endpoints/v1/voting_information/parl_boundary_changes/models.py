from dataclasses import dataclass, field
from typing import Optional

from polars import DataFrame
from static_data_helper import BaseDictDataclass, BaseResponse


@dataclass
class BaseParlBoundaryChange(BaseDictDataclass):
    current_constituencies_official_identifier: str
    current_constituencies_name: str
    new_constituencies_official_identifier: str
    new_constituencies_name: str

    @property
    def change_type(self):
        CHANGE_TYPE = []
        if self.new_constituencies_name != self.current_constituencies_name:
            CHANGE_TYPE.append("NAME_CHANGE")
        if (
            self.new_constituencies_official_identifier
            != self.current_constituencies_official_identifier
        ):
            CHANGE_TYPE.append("BOUNDARY_CHANGE")

        if CHANGE_TYPE:
            return "_".join(CHANGE_TYPE)
        return "NO_CHANGE"

    def as_dict(self):
        base = super().as_dict()
        base["CHANGE_TYPE"] = self.change_type
        return base

    @classmethod
    def from_row(cls, row: DataFrame):
        row_dict = row.to_dict(as_series=False)
        fields = [
            "current_constituencies_official_identifier",
            "current_constituencies_name",
            "new_constituencies_official_identifier",
            "new_constituencies_name",
        ]
        kwargs = {}
        try:
            for attr in fields:
                kwargs[attr] = row_dict[attr][0]
        except IndexError:
            return None
        return cls(**kwargs)


@dataclass
class BaseParlBoundariesResponse(BaseResponse):
    parl_boundary_changes: Optional[BaseParlBoundaryChange] = field(
        default=None
    )
