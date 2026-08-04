import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from analyzer import analyze


CLAUDE_RESULT = {"urgency": "normal", "consistency": "formed", "color": "brown"}


class SpeciesPromptTests(unittest.TestCase):
    def analyze_species(self, pet_type):
        response = SimpleNamespace(content=[SimpleNamespace(text=json.dumps(CLAUDE_RESULT))])
        with patch("analyzer.image_to_base64", return_value="image"), \
             patch("analyzer.anthropic.Anthropic") as client_class:
            client_class.return_value.messages.create.return_value = response
            result = analyze("sample.jpg", pet_type)
            request = client_class.return_value.messages.create.call_args.kwargs
        prompt = request["messages"][0]["content"][1]["text"]
        return result, prompt

    def test_dog_upload_uses_dog_prompt(self):
        result, prompt = self.analyze_species("dog")
        self.assertIn("DOG stool", prompt)
        self.assertEqual(result["urgency"], "normal")

    def test_cat_upload_uses_cat_prompt(self):
        result, prompt = self.analyze_species("cat")
        self.assertIn("CAT stool", prompt)
        self.assertEqual(result["urgency"], "normal")

    def test_both_species_return_the_same_structure(self):
        dog, _ = self.analyze_species("dog")
        cat, _ = self.analyze_species("cat")
        self.assertEqual(set(dog), set(cat))


if __name__ == "__main__":
    unittest.main()
