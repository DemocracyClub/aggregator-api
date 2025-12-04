from dataclasses import dataclass

import pytest
from starlette.requests import Request

from common.query_string import clean_query_params


@dataclass
class TestConfig:
    bool_param: bool = False
    str_param1: str = ""
    str_param2: str = "default"


@pytest.mark.parametrize(
    "qs",
    [
        "bool_param=true",
        "bool_param=TRUE",
        "bool_param=1",
    ],
)
def test_clean_query_params_bool_truthy(qs):
    req = Request(
        {
            "type": "http",
            "path": "/foo",
            "scheme": "https",
            "query_string": qs,
        }
    )
    params = clean_query_params(req, TestConfig)
    assert params.bool_param


@pytest.mark.parametrize(
    "qs",
    [
        "bool_param=false",
        "bool_param=0",
        "bool_param=arbitrarystring",
        "bool_param==",
        "bool_param",
        "",
    ],
)
def test_clean_query_params_bool_falsy(qs):
    req = Request(
        {
            "type": "http",
            "path": "/foo",
            "scheme": "https",
            "query_string": qs,
        }
    )
    params = clean_query_params(req, TestConfig)
    assert not params.bool_param


def test_clean_query_params_string_value():
    req = Request(
        {
            "type": "http",
            "path": "/foo",
            "scheme": "https",
            "query_string": "str_param1=value",
        }
    )
    params = clean_query_params(req, TestConfig)
    assert params.str_param1 == "value"


def test_clean_query_params_string_default():
    req = Request(
        {
            "type": "http",
            "path": "/foo",
            "scheme": "https",
            "query_string": "",
        }
    )
    params = clean_query_params(req, TestConfig)
    assert params.str_param1 == ""
    assert params.str_param2 == "default"


@pytest.mark.parametrize(
    "qs",
    [
        "str_param2=",
        "str_param2",
    ],
)
def test_clean_query_params_string_empty(qs):
    req = Request(
        {
            "type": "http",
            "path": "/foo",
            "scheme": "https",
            "query_string": qs,
        }
    )
    params = clean_query_params(req, TestConfig)
    # in this situation, str_param2 is explicitly empty string in the query string
    # so that overrides the default value on the class
    assert params.str_param2 == ""
