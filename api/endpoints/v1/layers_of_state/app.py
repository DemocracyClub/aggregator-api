import re
from pathlib import Path
from typing import IO
from urllib.parse import urljoin

import polars
from botocore.exceptions import ClientError
from mangum import Mangum
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from common.conf import settings
from common.middleware import MIDDLEWARE
from common.sentry_helper import init_sentry

init_sentry()


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


def get_file(postcode: Postcode) -> Path | IO:
    """
    Given an outcode, return a file-like object or path for Polars to read

    """

    root_path = "s3://ee.public.data/layers-of-state/by_outcode"
    file_path = f"{postcode.outcode}.parquet"

    full_path = urljoin(root_path, file_path)
    if root_path.startswith("s3://"):
        bucket_name = root_path.split("/")[2]
        key = "/".join(root_path.split("/")[3:]) + f"/{file_path}"
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


def df_to_address_picker(request, df):
    addresses = []

    for row in df.iter_rows(named=True):
        addresses.append(
            {
                "address": row["address"],
                "postcode": row["postcode"],
                "slug": str(row["uprn"]),
                "url": str(
                    request.url_for(
                        "layers_of_state_uprn",
                        postcode=row["postcode"].replace(" ", ""),
                        uprn=row["uprn"],
                    )
                ),
            },
        )
    return addresses


def get_layers(request, postcode: Postcode, uprn=None):
    ret = {
        "admin_ids": [],
        "address_picker": False,
        "addresses": [],
    }
    try:
        file_obj = get_file(postcode)
    except FileNotFoundError:
        return ret

    df = polars.read_parquet(file_obj)

    df = df.with_columns(
        polars.col("admin_ids").cast(polars.List(polars.Utf8)).list.join(",")
    )

    print(df)

    if uprn:
        df = df.filter((polars.col("uprn") == uprn))
        ret["admin_ids"] = df["admin_ids"][0].split(",")
        return ret

    df = df.filter((polars.col("postcode") == postcode.with_space))
    if df.is_empty():
        # This file doesn't have any rows matching the given postcode
        # Just return an empty list as this means there aren't elections here.
        return ret

    is_split = df.select(polars.col("admin_ids").n_unique()).to_series()[0] > 1

    if is_split:
        ret["address_picker"] = True
        ret["addresses"] = df_to_address_picker(request, df)
        return ret
    ret["admin_ids"] = df["admin_ids"][0].split(",")
    return ret


def layer_postcode_response(request: Request):
    postcode = Postcode(request.path_params["postcode"])
    layers = get_layers(request, postcode)
    return JSONResponse(layers)


def layer_uprn_response(request):
    postcode = Postcode(request.path_params["postcode"])
    uprn = request.path_params["uprn"]
    layers = get_layers(request, postcode, uprn=uprn)
    return JSONResponse(layers)


routes = [
    Route(
        "/api/v1/layers_of_state/postcode/{postcode}/",
        layer_postcode_response,
        methods=["GET"],
        name="layers_of_state_postcode",
    ),
    Route(
        "/api/v1/layers_of_state/postcode/{postcode}/{uprn}/",
        layer_uprn_response,
        methods=["GET"],
        name="layers_of_state_uprn",
    ),
]
app = Starlette(debug=settings.DEBUG, routes=routes, middleware=MIDDLEWARE)

handler = Mangum(app)
