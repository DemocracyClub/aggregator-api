from dataclasses import dataclass


@dataclass
class QueryParams:
    include_accessibility: bool = False
    include_current: bool = False
    recall_petition: bool = False
    boundary_reviews: bool = False
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""
    auth_token: str = ""
