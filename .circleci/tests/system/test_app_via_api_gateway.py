import hashlib
import re
import urllib
from urllib.parse import urljoin

from test_helpers import make_request


def test_app_front_page_http_200(frontend_url):
    resp = make_request(frontend_url)
    assert resp.status_code == 200


def test_api_postcode_can_include_urlencoded_spaces(api_url, tmp_api_user):
    base_url = urljoin(api_url, "api/v1/postcode/OX3 7LR/")
    resp = make_request(f"{base_url}?auth_token={tmp_api_user.api_key}")
    assert resp.status_code == 200


def test_api_docs_assets_style_css_filename_contains_md5_of_content(
    frontend_url,
):
    resp = make_request(urllib.parse.urljoin(frontend_url, "api/v1/"))
    styles_path_re = re.search('"([^"]+/styles.[a-f0-9]{12}.css)', resp.text)
    assert styles_path_re, "No CSS path found in content"
    styles_path = styles_path_re.group(1)
    styles_file = make_request(frontend_url + styles_path)
    content_md5_start = hashlib.md5(styles_file.content).hexdigest()[:12]
    assert f".{content_md5_start}." in styles_path


def test_sandbox_responses(api_url):
    base_url = urljoin(api_url, "api/v1/sandbox/postcode/AA11AA/")
    resp = make_request(base_url)
    assert resp.status_code == 200
