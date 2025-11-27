from dataclasses import dataclass


@dataclass
class QueryParams:
    include_accessibility: bool = False
    include_current: bool = False
    recall_petition: bool = False
