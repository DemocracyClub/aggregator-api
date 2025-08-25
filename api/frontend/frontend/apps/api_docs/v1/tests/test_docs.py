import json

import pytest
from bs4 import BeautifulSoup
from response_builder.v1.models.base import RootModel

"""
This test is not the most conceptually nice test, but it is useful

We're going to:
- scrape the docs for code blocks we want to validate
- parse each one as json
- validate the json against the response builder schema
"""


def get_code_blocks():
    with open(
        "api/frontend/frontend/apps/api_docs/v1/templates/api_docs_rendered.html",
        "r",
        encoding="utf-8",
    ) as file:
        html = file.read()

    soup = BeautifulSoup(html, "html.parser")

    code_blocks = []

    divs = (
        soup.find("h2", id="postcode-search-2")
        .find_parent("div")
        .find_all("div", class_="api-action-body")
    )
    for div in divs:
        if "Body:" in div.get_text():
            pre = div.find("pre")
            if pre:
                code = pre.find("code")
                if code:
                    code_blocks.append(code.get_text(strip=False))

    assert len(code_blocks) >= 4

    return code_blocks


code_blocks = get_code_blocks()


@pytest.mark.parametrize("code_block", code_blocks)
def test_docs(code_block):
    parsed_code_block = json.loads(code_block)
    model = RootModel.from_api_response(parsed_code_block)
    assert json.loads(model.json()) == parsed_code_block
