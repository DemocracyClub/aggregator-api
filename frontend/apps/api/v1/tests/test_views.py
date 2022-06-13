from django.test import TestCase


class PostcodeTest(TestCase):
    def test_cors_header(self):
        resp = self.client.get(
            "/api/v1/sandbox/postcode/AA11AA/", HTTP_ORIGIN="foo.bar/baz"
        )
        self.assertEqual(resp.get("Access-Control-Allow-Origin"), "*")
