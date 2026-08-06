import io
import os
import unittest
from unittest.mock import patch

from PIL import Image

from app import API_KEY_ENV_VAR, API_KEY_HEADER, DISCLOSURE_VERSION, _analyze_requests, app
from models import Analysis, db

TEST_API_KEY = "test-suite-api-key"


def upload(pet_type=None, query=""):
    image = io.BytesIO()
    Image.new("RGB", (2, 2), "brown").save(image, "JPEG")
    image.seek(0)
    data = {"photo": (image, "sample.jpg", "image/jpeg"),
            "disclosure_accepted": "true", "disclosure_version": DISCLOSURE_VERSION}
    if pet_type is not None:
        data["pet_type"] = pet_type
    return data, query


class PetTypeValidationTests(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        _analyze_requests.clear()
        with app.app_context():
            db.drop_all()
            db.create_all()
        self.client = app.test_client()
        self._env_patch = patch.dict(os.environ, {API_KEY_ENV_VAR: TEST_API_KEY})
        self._env_patch.start()
        self.addCleanup(self._env_patch.stop)
        self.auth_headers = {API_KEY_HEADER: TEST_API_KEY}

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    @patch("app.analyze", return_value={"urgency": "normal"})
    def test_dog_query_parameter_is_stored(self, _mock):
        data, _ = upload()
        response = self.client.post("/analyze?pet_type=dog", data=data,
                                    content_type="multipart/form-data", headers=self.auth_headers)
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Analysis.query.one().pet_type.value, "dog")

    @patch("app.analyze", return_value={"urgency": "normal"})
    def test_cat_form_parameter_is_stored(self, _mock):
        data, _ = upload("cat")
        response = self.client.post(
            "/analyze", data=data, content_type="multipart/form-data", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Analysis.query.one().pet_type.value, "cat")

    def test_invalid_pet_type_is_rejected(self):
        data, _ = upload("hamster")
        response = self.client.post(
            "/analyze", data=data, content_type="multipart/form-data", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("dog", response.get_json()["error"])

    @patch("app.analyze", return_value={"urgency": "normal"})
    def test_omitted_pet_type_defaults_to_dog(self, _mock):
        data, _ = upload()
        response = self.client.post(
            "/analyze", data=data, content_type="multipart/form-data", headers=self.auth_headers
        )
        self.assertEqual(response.status_code, 200)
        with app.app_context():
            self.assertEqual(Analysis.query.one().pet_type.value, "dog")


if __name__ == "__main__":
    unittest.main()
