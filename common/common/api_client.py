from abc import ABC


class BaseAPIClient(ABC):
    def __init__(self, base_url="") -> None:
        self.base_url: str = base_url
