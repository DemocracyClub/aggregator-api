import requests


def test_api_docs_assets_dont_contain_prod_path_prefix(public_url):
    resp = requests.get(public_url + "/api/v1/")
    assert resp.status_code == 200
    assert 'href="/Prod/' not in resp.text
    assert 'src="/Prod/' not in resp.text


def test_public_front_page_http_200(public_url):
    resp = requests.get(public_url)
    assert resp.status_code == 200


def test_cdn_front_page_http_200(cdn_url):
    resp = requests.get(cdn_url)
    assert resp.status_code == 200
