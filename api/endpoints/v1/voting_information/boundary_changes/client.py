import json
from pathlib import Path

import polars
from polars import DataFrame
from static_data_helper import AddressModel, FileNotFoundError, StaticDataHelper

from common.conf import settings

from .models import (
    BaseBoundaryReviewsResponse,
    BoundaryReviewModel,
)


class BoundaryReviewsApiClient(StaticDataHelper):
    def get_bucket_name(self):
        return "pollingstations.private.data"

    def get_file_path(self):
        data_path = Path(settings.BOUNDARY_REVIEWS_DATA_KEY_PREFIX)
        return data_path / self.get_shard_key()

    def is_split(self, data: DataFrame) -> bool:
        """
        Check if addresses in the postcode have different boundary reviews.
        """
        # If the postcode doesn't exist in the parquet file it's not split
        if data.is_empty():
            return False

        # Get unique boundary_reviews values
        # boundary_reviews is a List[String] column, so we need to compare the lists
        unique_reviews = data.select("boundary_reviews").unique()

        # If there are no boundary reviews it's not split
        # If there's one unique boundary review object it's not split
        # If there's more than one unique boundary review object it is split.
        return unique_reviews.height > 1

    def parse_boundary_reviews(self, boundary_reviews_list: list) -> list:
        """
        Parse the list of JSON strings into BoundaryReviewModel objects.
        """
        if not boundary_reviews_list:
            return []

        return [
            BoundaryReviewModel.from_dict(json.loads(review_json))
            for review_json in boundary_reviews_list
        ]

    def query_to_dict(self, data: DataFrame):
        if data.is_empty():
            return None

        resp = BaseBoundaryReviewsResponse()

        if self.is_split(data):
            resp.address_picker = True
            resp.addresses = [
                AddressModel.from_row(row, self.request)
                for row in data.to_dicts()
            ]
        else:
            # Not split so get reviews from the first row.
            raw_boundary_reviews: polars.Series = data[0, "boundary_reviews"]
            # to_list() returns [["json1", "json2", ...]] so we need [0] to get the inner list
            boundary_reviews_list = raw_boundary_reviews.to_list()
            resp.boundary_reviews = self.parse_boundary_reviews(
                boundary_reviews_list
            )

        return resp.as_dict()

    def patch_response(self, resp):
        try:
            return super().patch_response(
                resp
            )  # ToDo This isn't right, there's a load of patching of electoral services data etc in the super method. Need to fix.
        except FileNotFoundError:
            resp["boundary_reviews"] = None
            return resp
