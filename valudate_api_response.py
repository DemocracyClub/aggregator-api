import argparse
import json
from pathlib import Path

import requests
from response_builder.v1.models.base import RootModel

ENDPOINTS_ROOT = "api/endpoints/v1"


def validate_voting_information(postcode):
    url = f"http://localhost:8000/api/v1/postcode/{postcode}/"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return
    except json.JSONDecodeError as e:
        print(f"Failed to decode JSON: {e}")
        return
    print(data)
    print(RootModel.validate(data))


def main():
    endpoints = {
        path.name: path
        for path in Path(ENDPOINTS_ROOT).glob("*")
        if path.is_dir() and not path.name.startswith("_")
    }

    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Fetch and validate JSON data from an endpoint. "
        "Needs local API to be running in a different process."
    )
    parser.add_argument(
        "--endpoint",
        type=str,
        help="The API endpoint to query",
        choices=endpoints,
        required=True,
    )
    parser.add_argument(
        "--postcode",
        type=str,
        help="The postcode to use in the query",
        required=True,
    )
    args = parser.parse_args()

    if args.endpoint == "voting_information":
        validate_voting_information(args.postcode)


if __name__ == "__main__":
    main()
