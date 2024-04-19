"""
Helpers for getting data from S3
"""
import re
from pathlib import Path
from typing import IO, List, Tuple
from urllib.parse import urljoin

import httpx
import polars
from botocore.exceptions import ClientError
from common.async_requests import AsyncRequester
from common.conf import settings
from starlette.requests import Request


def ballot_paper_id_to_static_url(ballot_paper_id):
    parts = ballot_paper_id.split(".")
    path = "/".join((parts[-1], parts[0], parts[1], f"{ballot_paper_id}.json"))
    return urljoin(settings.WCIVF_BALLOT_CACHE_URL, path)


class Postcode:
    # TODO: DRY this up by moving it to `common`
    def __init__(self, postcode: str):
        self.postcode = re.sub("[^A-Z0-9]", "", str(postcode)[:10].upper())

    @property
    def with_space(self):
        return self.postcode[:-3] + " " + self.postcode[-3:]

    @property
    def without_space(self):
        return self.postcode

    @property
    def outcode(self):
        return self.with_space.split()[0]

    def __str__(self):
        return self.without_space


class ElectionsForPostcodeHelper:
    def __init__(
        self,
        postcode: str,
        request: Request,
        uprn: str = None,
        root_path: str = None,
        full_ballots: bool = True,
    ):
        """
        Args:
            postcode (str): The postcode for the location. This is converted internally to a `Postcode` object.
            request (Request): The Starlette request. Used for making URLs
            uprn (str, optional): The Unique Property Reference Number for a specific property. Defaults to None.
            root_path (str, optional): The root directory path where election data is stored. If not provided,
                                       the default path is taken from `settings.ELECTIONS_DATA_PATH`.
                                       Can be a local file path or an S3 URL starting `s3://`
            full_ballots (bool, optional): Flag to determine if full ballot details should be used. Defaults to True.
                                           If False then only ballot paper IDs are returned

        """

        self.postcode = Postcode(postcode)
        self.request = request
        self.uprn = uprn
        if not root_path:
            root_path = settings.ELECTIONS_DATA_PATH
        self.root_path = root_path
        self.full_ballots = full_ballots

    def get_file_path(self):
        return f"{self.root_path}/{self.postcode.outcode}.parquet"

    def get_file(self, file_path) -> Path | IO:
        full_path = urljoin(self.root_path, file_path)
        if full_path.startswith("s3://"):
            bucket_name = full_path.split("/")[2]
            key = "/".join(full_path.split("/")[3:])
            try:
                response = settings.S3_CLIENT.get_object(
                    Bucket=bucket_name, Key=key
                )
            except ClientError as ex:
                if ex.response["Error"]["Code"] == "NoSuchKey":
                    # If there's no key for whatever reason raise
                    raise FileNotFoundError(key)
                # Raise any other boto3 errors
                raise
            return response["Body"].read()
        return Path(full_path)

    def addresses_to_address_objects(self, df):
        addresses = []

        for row in df.iter_rows(named=True):
            addresses.append(
                {
                    "address": row["address"],
                    "postcode": row["postcode"],
                    "slug": str(row["uprn"]),
                    "url": str(
                        self.request.url_for(
                            "elections_for_uprn",
                            postcode=row["postcode"].replace(" ", ""),
                            uprn=row["uprn"],
                        )
                    ),
                },
            )
        return addresses

    def get_ballot_list(self) -> Tuple[bool, List]:
        df = polars.read_parquet(self.get_file(self.get_file_path()))
        if "ballot_ids" in df.columns:
            # TODO Remove this if we change the name at source
            df = df.rename({"ballot_ids": "current_elections"})

        # TODO: This isn't needed if the Parquet casts the list to a string
        #       at the point of creation
        df = df.with_columns(
            polars.col("current_elections")
            .cast(polars.List(polars.Utf8))
            .list.join(",")
        )

        if self.uprn:
            df = df.filter((polars.col("uprn") == self.uprn))
            return False, df["current_elections"][0].split(",")

        df = df.filter((polars.col("postcode") == self.postcode.with_space))

        # Count the unique values in the `ballot_ids` column.
        # If there is more than one value, count the postcode as split
        is_split = (
            df.select(polars.col("current_elections").n_unique()).to_series()[0]
            > 1
        )

        if is_split:
            return is_split, self.addresses_to_address_objects(df)

        return is_split, df["current_elections"][0].split(",")

    async def get_full_ballots(self, ballot_data):
        request_dict = {}

        for ballot in ballot_data:
            ballot_id = ballot["ballot_paper_id"]
            url = ballot_paper_id_to_static_url(ballot_id)
            request_dict[ballot_id] = {
                "url": url,
                "params": {},  # Add any params if needed
                "headers": {},  # Custom headers can be added here if required
            }
        requester = AsyncRequester(request_dict=request_dict)
        response_dict = await requester.get_urls(raise_errors=False)
        result = []
        for key, value in response_dict.items():
            response: httpx.Response = value["response"]
            if response.is_success:
                result.append(response.json())
        return result

    async def ballot_list_to_dates(self, ballot_list):
        ballot_data = [{"ballot_paper_id": ballot} for ballot in ballot_list]
        if self.full_ballots:
            ballot_data = await self.get_full_ballots(ballot_data)

        ballots_by_date = {}
        for ballot in ballot_data:
            ballot_date = ballot["ballot_paper_id"].rsplit(".", 1)[-1]
            if ballot_date not in ballots_by_date:
                ballots_by_date[ballot_date] = []
            ballots_by_date[ballot_date].append(ballot)

        dates_list = []
        for date, ballots in ballots_by_date.items():
            dates_list.append({"date": date, "ballots": ballots})
        return sorted(dates_list, key=lambda date: date["date"])

    async def build_response(self):
        is_split, data_for_postcode = self.get_ballot_list()
        data = {
            "address_picker": is_split,
            "addresses": [],
        }

        if is_split:
            data["addresses"] = data_for_postcode
        else:
            data["dates"] = await self.ballot_list_to_dates(data_for_postcode)

        return data
