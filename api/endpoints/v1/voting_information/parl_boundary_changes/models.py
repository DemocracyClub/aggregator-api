from dataclasses import dataclass
from typing import List

from polars import DataFrame
from static_data_helper import BaseDictDataclass


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

@dataclass(eq=True, unsafe_hash=True)
class BoundaryReviewDetailsModel(BaseDictDataclass):
    consultation_url: str
    effective_date: str
    legislation_title: str
    organisation_name: str
    organisation_official_name: str
    organisation_gss: str

@dataclass(eq=True, unsafe_hash=True)
class BoundaryReviewModel(BaseDictDataclass):
    boundary_review_id: str
    boundary_review_details: BoundaryReviewDetailsModel
    boundary_changes: List[BoundaryChangeModel]


# Example value from boundary_reviews field in parquet file
# [{
#     "boundary_review_id": 964,
#     "boundary_review_details": {
#         "consultation_url": "https://boundaries.scot/reviews/second-review-scottish-parliament-boundaries",
#         "effective_date": "2026-05-07",
#         "legislation_title": "The Scottish Parliament (Constituencies and Regions) Order 2025"},
#         "organisation_gss":"S92000003",
#         "organisation_name":"Scottish Parliament",
#         "organisation_official_name":"Scottish Parliament"
#     "changes": [
#         {
#             "change_scenario": "BOUNDARY_CHANGED",
#             "division_type": "SPE",
#             "new_division_official_identifier": "gss:S17000026",
#             "new_division_slug": "north-east-scotland",
#             "new_divisionset_pmtiles_url": "https://s3.eu-west-2.amazonaws.com/ee.public.data/pmtiles-store/sp_822_473a12b927395fe33fa9981a79dc46c9.pmtiles",
#             "old_division_official_identifier": "gss:S17000014",
#             "old_division_slug": "north-east-scotland",
#             "old_divisionset_pmtiles_url": "https://s3.eu-west-2.amazonaws.com/ee.public.data/pmtiles-store/sp_23_205aef99ea4c56b0b99e9cb9edd2fb49.pmtiles"
#         },
#         {
#             "change_scenario": "NO_CHANGE",
#             "division_type": "SPC",
#             "new_division_official_identifier": "gss:S16000151",
#             "new_division_slug": "aberdeen-central",
#             "new_divisionset_pmtiles_url": "https://s3.eu-west-2.amazonaws.com/ee.public.data/pmtiles-store/sp_822_473a12b927395fe33fa9981a79dc46c9.pmtiles",
#             "old_division_official_identifier": "gss:S16000074",
#             "old_division_slug": "aberdeen-central",
#             "old_divisionset_pmtiles_url": "https://s3.eu-west-2.amazonaws.com/ee.public.data/pmtiles-store/sp_23_205aef99ea4c56b0b99e9cb9edd2fb49.pmtiles"
#         }
#     ]
# }]
