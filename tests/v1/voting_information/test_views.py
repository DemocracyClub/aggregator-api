from sandbox import app
from starlette.testclient import TestClient


def test_cors_header():
    client = TestClient(app.app)

    resp = client.get(
        "/api/v1/sandbox/postcode/AA11AA/", headers={"Origin": "example.com"}
    )
    assert resp.headers.get("Access-Control-Allow-Origin") == "*"
