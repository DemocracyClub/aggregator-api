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
    ballots: List[str]

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
            ballots=data.get("ballots", []),
        )


@dataclass(eq=True, unsafe_hash=True)
class BoundaryReviewModel(BaseDictDataclass):
    id: str
    consultation_url: str
    effective_date: str
    legislation_title: str
    organisation_name: str
    organisation_official_name: str
    organisation_gss: str
    boundary_changes: List[BoundaryChangeModel]

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            id=str(data["boundary_review_id"]),
            consultation_url=data["boundary_review_details"][
                "consultation_url"
            ],
            effective_date=data["boundary_review_details"]["effective_date"],
            legislation_title=data["boundary_review_details"][
                "legislation_title"
            ],
            organisation_name=data["boundary_review_details"][
                "organisation_name"
            ],
            organisation_official_name=data["boundary_review_details"][
                "organisation_official_name"
            ],
            organisation_gss=data["boundary_review_details"][
                "organisation_gss"
            ],
            boundary_changes=[
                BoundaryChangeModel.from_dict(change)
                for change in data["changes"]
            ],
        )


@dataclass
class BaseBoundaryReviewsResponse(BaseResponse):
    boundary_reviews: Optional[List[BoundaryReviewModel]] = field(default=None)
