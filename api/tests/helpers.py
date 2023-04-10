import json
from pathlib import Path

from common import settings


def load_fixture(testname, fixture, api_version="v1"):
    dirname = Path(__file__).parent
    file_path: Path = (
        dirname / api_version / "test_data" / testname / f"{fixture}.json"
    )
    if not file_path.exists():
        return []
    with file_path.open("r") as f:
        return json.loads(f.read())


def load_fixture_by_url(testname, url):
    if settings.WDIV_BASE_URL in url:
        return load_fixture(f"{testname}", "wdiv")
    if settings.WCIVF_BASE_URL in url:
        return load_fixture(f"{testname}", "wcivf")
    if settings.EE_BASE_URL in url:
        return load_fixture(f"{testname}", "ee")
    raise Exception(f"Could not find fixture for {url}")


def load_sandbox_output(filename, base_url=None, api_version="v1"):
    dirname = Path(__file__).parent.parent / "endpoints"
    file_path: Path = (
        dirname / api_version / "sandbox" / f"sandbox-responses/{filename}.json"
    )
    with open(file_path, "r") as f:
        json_str = f.read()
        if base_url:
            json_str = json_str.replace(
                "https://developers.democracyclub.org.uk/api/v1/sandbox/",
                base_url,
            )
        return json.loads(json_str)


def mock_proxy_single_request(fixture_name, loop, request):
    return {
        "url": request.url,
        "status": 200,
        "json": load_fixture_by_url(fixture_name, request.url),
    }


def mock_proxy_multiple_requests(fixture_name, loop, *requests):
    return [
        {
            "url": req.url,
            "status": 200,
            "json": load_fixture_by_url(fixture_name, req.url),
        }
        for req in requests
    ]


fixture_map = {
    "AA11AA": "addresspc_endpoints/test_no_elections",
    "AA12AA": "addresspc_endpoints/test_one_election_station_known_with_candidates",
    "AA12AB": "addresspc_endpoints/test_one_election_station_not_known_with_candidates",
    "AA13AA": "addresspc_endpoints/test_address_picker",
    "AA14AA": "addresspc_endpoints/test_multiple_elections",
}
