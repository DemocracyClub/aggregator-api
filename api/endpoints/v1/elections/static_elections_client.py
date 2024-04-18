"""
Helpers for getting data from S3
"""
import re
from pathlib import Path
from typing import IO, List, Tuple
from urllib.parse import urljoin

import polars
from botocore.exceptions import ClientError
from common.conf import settings


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
    def __init__(self, postcode: str, uprn: str = None, root_path: str = None):
        """

        :type root_path: str, Either a file or S3 path to the root of the data
        """
        self.postcode = Postcode(postcode)
        self.uprn = uprn
        if not root_path:
            root_path = settings.ELECTIONS_DATA_PATH
        self.root_path = root_path

    def get_file_path(self):
        return f"{self.root_path}/{self.postcode.outcode}.parquet"

    def get_file(self, file_path) -> Path | IO:
        full_path = urljoin(self.root_path, file_path)
        if full_path.startswith("s3://"):
            bucket_name = full_path.split("/")[2]
            key = "/".join(full_path.split("/")[3:])
            try:
                response = settings.S3_CLIENT.get_object(bucket_name, key)
            except ClientError as ex:
                if ex.response["Error"]["Code"] == "NoSuchKey":
                    # If there's no key for whatever reason raise
                    raise FileNotFoundError()
                # Raise any other boto3 errors
                raise
            return response["Body"].read()
        return Path(full_path)

    def get_ballot_list(self) -> Tuple[bool, List]:
        df = polars.read_parquet(self.get_file(self.get_file_path())).filter(
            (polars.col("postcode") == self.postcode.with_space)
        )

        # Count the unique values in the `current_elections` column.
        # If there is more than one value, count the postcode as split
        is_split = (
            df.select(polars.col("current_elections").n_unique()).to_series()[0]
            > 1
        )

        if is_split:
            # TODO: support split postcodes
            raise NotImplementedError("Split postcodes not supported yet")

        return is_split, df["current_elections"][0].split(",")

    def ballot_list_to_dates(self, ballot_list):
        ballots_by_date = {}
        for ballot in ballot_list:
            ballot_date = ballot.rsplit(".", 1)[-1]
            if ballot_date not in ballots_by_date:
                ballots_by_date[ballot_date] = []
            ballots_by_date[ballot_date].append(ballot)

        dates_list = []
        for date, ballots in ballots_by_date.items():
            dates_list.append({"date": date, "ballots": ballots})
        return sorted(dates_list, key=lambda date: date["date"])

    def build_response(self):
        is_split, data_for_postcode = self.get_ballot_list()
        data = {
            "address_picker": is_split,
            "addresses": [],
        }

        if is_split:
            data["addresses"] = data_for_postcode
        else:
            data["dates"] = self.ballot_list_to_dates(data_for_postcode)

        return data
