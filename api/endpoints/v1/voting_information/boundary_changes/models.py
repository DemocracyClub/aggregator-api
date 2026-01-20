from dataclasses import dataclass, field
from typing import List, Optional

from static_data_helper import BaseDictDataclass, BaseResponse


@dataclass(eq=True, unsafe_hash=True)
class BoundaryChangeModel(BaseDictDataclass):
    change_scenario: str
    division_type: str
    new_division_official_identifier: str
    new_division_slug: str
    new_divisionset_pmtiles_url: str
    old_division_official_identifier: str
    old_division_slug: str
    old_divisionset_pmtiles_url: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            change_scenario=data["change_scenario"],
            division_type=data["division_type"],
            new_division_official_identifier=data[
                "new_division_official_identifier"
            ],
            new_division_slug=data["new_division_slug"],
            new_divisionset_pmtiles_url=data["new_divisionset_pmtiles_url"],
            old_division_official_identifier=data[
                "old_division_official_identifier"
            ],
            old_division_slug=data["old_division_slug"],
            old_divisionset_pmtiles_url=data["old_divisionset_pmtiles_url"],
        )


@dataclass(eq=True, unsafe_hash=True)
class BoundaryReviewDetailsModel(BaseDictDataclass):
    consultation_url: str
    effective_date: str
    legislation_title: str
    organisation_name: str
    organisation_official_name: str
    organisation_gss: str

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            consultation_url=data["consultation_url"],
            effective_date=data["effective_date"],
            legislation_title=data["legislation_title"],
            organisation_name=data["organisation_name"],
            organisation_official_name=data["organisation_official_name"],
            organisation_gss=data["organisation_gss"],
        )


@dataclass(eq=True, unsafe_hash=True)
class BoundaryReviewModel(BaseDictDataclass):
    boundary_review_id: str
    boundary_review_details: BoundaryReviewDetailsModel
    boundary_changes: List[BoundaryChangeModel]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            boundary_review_id=str(data["boundary_review_id"]),
            boundary_review_details=BoundaryReviewDetailsModel.from_dict(
                data["boundary_review_details"]
            ),
            boundary_changes=[
                BoundaryChangeModel.from_dict(change)
                for change in data["changes"]
            ],
        )


@dataclass
class BaseBoundaryReviewsResponse(BaseResponse):
    boundary_reviews: Optional[List[BoundaryReviewModel]] = field(default=None)
