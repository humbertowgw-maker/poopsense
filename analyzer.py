import json
import os
import re

import anthropic
from dotenv import load_dotenv

from image_handler import image_to_base64
from prompt import prompt_for

load_dotenv()

REQUIRED_DEFAULTS = {
    "image_quality": "poor", "image_quality_notes": "Analysis was unavailable.",
    "color": "unclear", "color_concerns": [], "consistency": "unclear",
    "stool_score": 0, "stool_score_confidence": "low", "shape_and_texture": "unclear",
    "segmentation": "unclear", "surface_texture": "unclear",
    "moisture_appearance": "unclear", "color_uniformity": "unclear",
    "estimated_amount": "unclear", "blood_visible": "unclear",
    "mucus_visible": "unclear", "coating_or_grease": "unclear",
    "parasite_like_material": "unclear", "foreign_material": "unclear",
    "undigested_material": "unclear", "hair_or_plant_material": "unclear",
    "surrounding_contamination": "unclear", "visible_findings": [],
    "possible_non_diagnostic_explanations": [], "urgency": "monitor",
    "urgency_reasons": [], "recommendation": "Contact your veterinarian if you are concerned.",
    "monitor_for": [], "questions_for_vet": [], "limitations": [],
    "body_area": "unclear", "skin_color": "unclear", "coat_condition": "unclear",
    "lesion_type": "unclear", "distribution": "unclear", "redness": "unclear",
    "swelling": "unclear", "discharge_or_bleeding": "unclear", "hair_loss": "unclear",
    "visible_parasite_like_material": "unclear",
}


def analyze(image_path, pet_type="dog", analysis_type="stool"):
    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1800,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                 "data": image_to_base64(image_path)}},
                {"type": "text", "text": prompt_for(pet_type, analysis_type)},
            ]}],
        )
        raw = "".join(block.text for block in message.content if getattr(block, "text", None))
        result = normalize_result(parse_json_response(raw))
        result["analysis_type"] = analysis_type
        return result
    except Exception:
        return fallback_result(pet_type, analysis_type)


def parse_json_response(raw):
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, str):
        raise ValueError("Claude response was not text")
    clean = re.sub(r"```(?:json)?", "", raw, flags=re.IGNORECASE).replace("```", "").strip()
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", clean):
        try:
            value, _ = decoder.raw_decode(clean[match.start():])
            if isinstance(value, dict):
                return value
        except json.JSONDecodeError:
            continue
    raise ValueError("No valid JSON object returned")


def normalize_result(result):
    normalized = dict(REQUIRED_DEFAULTS)
    normalized.update(result)
    return normalized


def fallback_result(pet_type, analysis_type="stool"):
    result = dict(REQUIRED_DEFAULTS)
    subject = "skin or coat" if analysis_type == "skin" else "stool"
    result["recommendation"] = (
        f"The {pet_type} {subject} photo could not be analyzed right now. "
        "Try another clear photo or contact your veterinarian."
    )
    result["analysis_type"] = analysis_type
    result["limitations"] = ["The AI vision service was unavailable; no visual assessment was completed."]
    result["analysis_unavailable"] = True
    return result
