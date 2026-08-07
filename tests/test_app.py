import io
import os
import unittest
from unittest.mock import patch

from PIL import Image

from app import API_KEY_ENV_VAR, API_KEY_HEADER, app, DISCLOSURE_VERSION
from models import db

TEST_API_KEY = "test-suite-api-key"


def valid_jpeg():
    payload = io.BytesIO()
    Image.new("RGB", (2, 2), "brown").save(payload, format="JPEG")
    payload.seek(0)
    return payload


class AnalyzeConsentTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = app.test_client()
        self._env_patch = patch.dict(os.environ, {API_KEY_ENV_VAR: TEST_API_KEY})
        self._env_patch.start()
        self.addCleanup(self._env_patch.stop)
        self.auth_headers = {API_KEY_HEADER: TEST_API_KEY}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_analysis_requires_disclosure_acceptance(self):
        response = self.client.post(
            "/analyze",
            data={"photo": (io.BytesIO(b"image"), "sample.jpg")},
            content_type="multipart/form-data",
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("safety notice", response.get_json()["error"])

    def test_home_includes_user_controlled_vet_report_sharing(self):
        response = self.client.get("/")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Share with vet", page)
        self.assertIn("The photo is not included automatically", page)
        self.assertIn("navigator.share", page)

    def test_home_reuses_the_pass_tip_jar(self):
        response = self.client.get("/")
        page = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn("Settings & support", page)
        self.assertIn("tip=brigade&amp;source=poopsense", page)
        self.assertIn("utm_source=poopsense", page)
        self.assertIn("utm_campaign=tip_jar", page)
        self.assertIn("PoopSense does not receive or store your card details", page)

    @patch("app.analyze")
    def test_analysis_accepts_current_disclosure(self, analyze_mock):
        analyze_mock.return_value = {"urgency": "monitor"}
        response = self.client.post(
            "/analyze",
            data={
                "photo": (valid_jpeg(), "sample.jpg", "image/jpeg"),
                "disclosure_accepted": "true",
                "disclosure_version": DISCLOSURE_VERSION,
            },
            content_type="multipart/form-data",
            headers=self.auth_headers,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["urgency"], "monitor")
        self.assertIn("not a veterinarian", response.get_json()["disclaimer"])


class VetFinderTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.app_context = app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_vet_search_requires_valid_coordinates(self):
        response = self.client.get("/vets?lat=unknown&lng=-122")

        self.assertEqual(response.status_code, 400)

    @patch("app.httpx.post")
    def test_vet_search_returns_emergency_and_navigation_links(self, post_mock):
        post_mock.return_value.raise_for_status.return_value = None
        post_mock.return_value.json.return_value = {
            "elements": [{
                "type": "node",
                "lat": 47.61,
                "lon": -122.33,
                "tags": {
                    "name": "Always Open Animal ER",
                    "amenity": "veterinary",
                    "opening_hours": "24/7",
                    "phone": "+1 206 555 0100",
                    "addr:housenumber": "100",
                    "addr:street": "Paw Street",
                    "addr:city": "Seattle",
                    "addr:state": "WA",
                },
            }]
        }

        response = self.client.get("/vets?lat=47.60&lng=-122.32")
        clinic = response.get_json()["clinics"][0]

        self.assertEqual(response.status_code, 200)
        self.assertTrue(clinic["is_24_hour"])
        self.assertIn("google.com/maps/dir", clinic["navigate_url"])
        self.assertEqual(clinic["phone"], "+1 206 555 0100")


if __name__ == "__main__":
    unittest.main()
