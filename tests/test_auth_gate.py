import io
import os
import unittest
from unittest.mock import patch

from PIL import Image

from app import API_KEY_ENV_VAR, API_KEY_HEADER, DISCLOSURE_VERSION, _analyze_requests, app
from models import db

TEST_API_KEY = "test-suite-api-key"


def valid_jpeg():
    payload = io.BytesIO()
    Image.new("RGB", (2, 2), "brown").save(payload, "JPEG")
    payload.seek(0)
    return payload


def analyze_payload():
    return {
        "photo": (valid_jpeg(), "sample.jpg", "image/jpeg"),
        "disclosure_accepted": "true",
        "disclosure_version": DISCLOSURE_VERSION,
    }


class ApiKeyGateTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        _analyze_requests.clear()
        with app.app_context():
            db.drop_all()
            db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_analyze_without_api_key_is_rejected(self):
        with patch.dict(os.environ, {API_KEY_ENV_VAR: TEST_API_KEY}):
            response = self.client.post(
                "/analyze", data=analyze_payload(), content_type="multipart/form-data"
            )

        self.assertEqual(response.status_code, 401)
        self.assertIn("API key", response.get_json()["error"])

    def test_analyze_with_wrong_api_key_is_rejected(self):
        with patch.dict(os.environ, {API_KEY_ENV_VAR: TEST_API_KEY}):
            response = self.client.post(
                "/analyze",
                data=analyze_payload(),
                content_type="multipart/form-data",
                headers={API_KEY_HEADER: "not-the-right-key"},
            )

        self.assertEqual(response.status_code, 401)

    @patch("app.analyze", return_value={"urgency": "normal"})
    def test_analyze_with_correct_api_key_is_accepted(self, _analyze_mock):
        with patch.dict(os.environ, {API_KEY_ENV_VAR: TEST_API_KEY}):
            response = self.client.post(
                "/analyze",
                data=analyze_payload(),
                content_type="multipart/form-data",
                headers={API_KEY_HEADER: TEST_API_KEY},
            )

        self.assertEqual(response.status_code, 200)

    def test_analyze_fails_closed_when_server_key_is_unconfigured(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop(API_KEY_ENV_VAR, None)
            response = self.client.post(
                "/analyze",
                data=analyze_payload(),
                content_type="multipart/form-data",
                headers={API_KEY_HEADER: "anything"},
            )

        self.assertEqual(response.status_code, 401)

    def test_portfolio_metrics_without_api_key_is_rejected(self):
        with patch.dict(os.environ, {API_KEY_ENV_VAR: TEST_API_KEY}):
            response = self.client.get("/portfolio-metrics")

        self.assertEqual(response.status_code, 401)

    def test_portfolio_metrics_with_correct_api_key_is_accepted(self):
        with patch.dict(os.environ, {API_KEY_ENV_VAR: TEST_API_KEY}):
            response = self.client.get(
                "/portfolio-metrics", headers={API_KEY_HEADER: TEST_API_KEY}
            )

        self.assertEqual(response.status_code, 200)

    def test_home_page_renders_configured_key_for_the_built_in_web_client(self):
        with patch.dict(os.environ, {API_KEY_ENV_VAR: TEST_API_KEY}):
            response = self.client.get("/")

        self.assertIn(f'const apiKey = "{TEST_API_KEY}"', response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
