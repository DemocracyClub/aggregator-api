from starlette.testclient import TestClient

from sandbox import app


def test_cors_header():
    client = TestClient(app.app)

    resp = client.get(
        "/api/v1/sandbox/postcode/AA11AA/", headers={"Origin": "example.com"}
    )
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"
