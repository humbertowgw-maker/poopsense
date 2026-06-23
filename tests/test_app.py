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


if __name__ == "__main__":
    unittest.main()
