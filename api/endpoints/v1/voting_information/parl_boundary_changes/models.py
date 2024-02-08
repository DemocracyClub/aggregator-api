from dataclasses import dataclass, field
from typing import List, Optional

from s3_select_helper import AddressModel, BaseDictDataclass


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


@dataclass
class BaseParlBoundariesResponse(BaseDictDataclass):
    parl_boundary_changes: Optional[BaseParlBoundaryChange] = field(
        default=None
    )
    addresses: Optional[List[AddressModel]] = field(default_factory=list)
    address_picker: bool = field(default=False)
