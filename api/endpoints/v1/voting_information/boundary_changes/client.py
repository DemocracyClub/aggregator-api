import json
import logging
from pathlib import Path

import polars
import sentry_sdk
from polars import DataFrame
from static_data_helper import AddressModel, FileNotFoundError, StaticDataHelper

from common.conf import settings

from .models import (
    BaseBoundaryReviewsResponse,
    BoundaryReviewModel,
)

logger = logging.getLogger(__name__)


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

    def query_to_dict(self, data: DataFrame) -> dict:
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
            boundary_reviews_list = raw_boundary_reviews.to_list()
            resp.boundary_reviews = self.parse_boundary_reviews(
                boundary_reviews_list
            )

        return resp.as_dict()

    def patch_response(self, resp: dict) -> dict:
        try:
            if self.uprn:
                boundary_review_response = self.uprn_response()
            else:
                boundary_review_response = self.postcode_response()

            if not boundary_review_response:
                # query_to_dict might return None if it didn't get any data
                return resp

            if boundary_review_response["address_picker"]:
                # Split boundary data - return address picker response
                # but preserve electoral_services, registration and postcode_location
                # Don't show dates, even though we might know them.
                boundary_review_response["dates"] = []
                boundary_review_response["postcode_location"] = resp.get(
                    "postcode_location"
                )
                boundary_review_response["electoral_services"] = resp.get(
                    "electoral_services"
                )
                boundary_review_response["registration"] = resp.get(
                    "registration"
                )
                return boundary_review_response

            # Not split - just add boundary_reviews to the existing response
            resp["boundary_reviews"] = boundary_review_response.get(
                "boundary_reviews"
            )
            return resp
        except FileNotFoundError as ex:
            # If we're missing a parquet file we want to know about this so log it, and raise in sentry.
            # But don't crash over it.
            logger.exception("Boundary Review File Not Found")
            sentry_sdk.capture_exception(ex)
            resp["boundary_reviews"] = []
            return resp
