import io
import unittest
from unittest.mock import patch

from app import app, DISCLOSURE_VERSION


class AnalyzeConsentTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def test_analysis_requires_disclosure_acceptance(self):
        response = self.client.post(
            "/analyze",
            data={"photo": (io.BytesIO(b"image"), "sample.jpg")},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("safety notice", response.get_json()["error"])

    @patch("app.analyze")
    def test_analysis_accepts_current_disclosure(self, analyze_mock):
        analyze_mock.return_value = {"urgency": "monitor"}
        response = self.client.post(
            "/analyze",
            data={
                "photo": (io.BytesIO(b"image"), "sample.jpg", "image/jpeg"),
                "disclosure_accepted": "true",
                "disclosure_version": DISCLOSURE_VERSION,
            },
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["urgency"], "monitor")
        self.assertIn("not a veterinarian", response.get_json()["disclaimer"])


class VetFinderTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

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
