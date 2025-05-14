import json

import pytest
from bs4 import BeautifulSoup
from response_builder.v1.models.base import RootModel


def extract_code_block(html, h4_id):
    soup = BeautifulSoup(html, "html.parser")

    # Find the <h4> element with the given id
    h4 = soup.find("h4", id=h4_id)
    if not h4:
        raise ValueError(f"Failed to find a h4 element with id {h4_id}")

    # Traverse the siblings after the h4
    for sibling in h4.find_all_next():
        if sibling.name == "div" and "api-action-body" in sibling.get(
            "class", []
        ):
            if "Body:" in sibling.get_text():
                code_tag = sibling.find("pre")
                if code_tag:
                    code = code_tag.find("code")
                    if code:
                        return code.get_text(strip=False)
            break

    raise ValueError("Failed to find desired code block")


"""
This test is not the most conceptually nice test, but it is useful

This list contains a list of id attributes of h4 elements
For each element in this list we're going to:
- scrape the docs for the relevant h4 element
- find the Body code block under it
- parse that as json
- validate the json against the response builder schema
"""
h4_ids = [
    "postcode-search-no-upcoming-ballots-4",
    "postcode-search-results-found-4",
    "postcode-search-address-picker-4",
    "address-search-4",
]


@pytest.mark.parametrize("h4_id", h4_ids)
def test_docs(h4_id):
    with open(
        "frontend/apps/api_docs/v1/templates/api_docs_rendered.html",
        "r",
        encoding="utf-8",
    ) as file:
        html = file.read()

    code_block = json.loads(extract_code_block(html, h4_id))
    model = RootModel.from_api_response(code_block)
    assert json.loads(model.json()) == code_block
