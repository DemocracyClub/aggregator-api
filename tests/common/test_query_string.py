from dataclasses import dataclass

import pytest
from starlette.requests import Request

from common.query_string import clean_query_params


@dataclass
class TestConfig:
    param1: bool = False


@pytest.mark.parametrize(
    "qs",
    [
        "param1=true",
        "param1=TRUE",
        "param1=1",
    ],
)
def test_clean_query_params_truthy(qs):
    req = Request(
        {
            "type": "http",
            "path": "/foo",
            "scheme": "https",
            "query_string": qs,
        }
    )
    params = clean_query_params(req, TestConfig)
    assert params.param1


@pytest.mark.parametrize(
    "qs",
    [
        "param1=false",
        "param1=0",
        "param1=arbitrarystring",
        "param1==",
        "param1",
    ],
)
def test_clean_query_params_falsy(qs):
    req = Request(
        {
            "type": "http",
            "path": "/foo",
            "scheme": "https",
            "query_string": qs,
        }
    )
    params = clean_query_params(req, TestConfig)
    assert not params.param1
