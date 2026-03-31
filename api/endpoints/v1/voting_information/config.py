from dataclasses import dataclass


@dataclass
class QueryParams:
    include_accessibility: bool = False
    include_current: bool = False
    recall_petition: bool = False
    include_boundary_reviews: bool = False
    include_2026_pilots: bool = False
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    auth_token: str = ""
