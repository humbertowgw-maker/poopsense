import anthropic
import os
import sys
import json
from dotenv import load_dotenv
from image_handler import image_to_base64
from prompt import VET_PROMPT

load_dotenv()

def analyze(image_path):
    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    b64_image = image_to_base64(image_path)
    
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": b64_image
                    }
                },
                {"type": "text", "text": VET_PROMPT}
            ]
        }]
    )
    raw = message.content[0].text
    clean = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)