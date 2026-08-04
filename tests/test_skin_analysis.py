import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

from analyzer import analyze
from app import DISCLOSURE_VERSION, _analyze_requests, app
from models import db


def valid_jpeg():
    payload = io.BytesIO()
    Image.new("RGB", (2, 2), "pink").save(payload, "JPEG")
    payload.seek(0)
    return payload


class SkinPromptTests(unittest.TestCase):
    def analyze_skin(self, pet_type):
        response = SimpleNamespace(content=[SimpleNamespace(text=json.dumps({
            "urgency": "monitor", "lesion_type": "redness", "body_area": "ear"
        }))])
        with patch("analyzer.image_to_base64", return_value="image"), \
             patch("analyzer.anthropic.Anthropic") as client_class:
            client_class.return_value.messages.create.return_value = response
            result = analyze("sample.jpg", pet_type, analysis_type="skin")
            request = client_class.return_value.messages.create.call_args.kwargs
        return result, request["messages"][0]["content"][1]["text"]

    def test_dog_skin_uses_dog_skin_prompt(self):
        result, prompt = self.analyze_skin("dog")
        self.assertIn("DOG skin", prompt)
        self.assertEqual(result["analysis_type"], "skin")

    def test_cat_skin_uses_cat_skin_prompt(self):
        result, prompt = self.analyze_skin("cat")
        self.assertIn("CAT skin", prompt)
        self.assertEqual(result["lesion_type"], "redness")


class SkinRouteTests(unittest.TestCase):
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

    def payload(self, analysis_type="skin"):
        return {
            "photo": (valid_jpeg(), "skin.jpg", "image/jpeg"),
            "pet_type": "cat",
            "analysis_type": analysis_type,
            "disclosure_accepted": "true",
            "disclosure_version": DISCLOSURE_VERSION,
        }

    @patch("app.analyze", return_value={"urgency": "monitor"})
    def test_skin_form_value_reaches_analyzer(self, analyze_mock):
        response = self.client.post("/analyze", data=self.payload(), content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["analysis_type"], "skin")
        self.assertEqual(analyze_mock.call_args.kwargs["analysis_type"], "skin")

    def test_invalid_analysis_type_is_rejected(self):
        response = self.client.post(
            "/analyze", data=self.payload("xray"), content_type="multipart/form-data"
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("stool", response.get_json()["error"])

    @patch("app.analyze", return_value={"urgency": "normal"})
    def test_omitted_analysis_type_defaults_to_stool(self, analyze_mock):
        data = self.payload()
        data.pop("analysis_type")
        response = self.client.post("/analyze", data=data, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["analysis_type"], "stool")
        self.assertEqual(analyze_mock.call_args.kwargs["analysis_type"], "stool")


if __name__ == "__main__":
    unittest.main()
