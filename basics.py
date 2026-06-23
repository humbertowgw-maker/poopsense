def analyze_poop(color, consistency):
    if color == "brown":
        return "Normal — looks healthy"
    elif color == "black":
        return "Warning — see a vet"
    else:
        return "Monitor closely"

result = analyze_poop("brown", "solid")
print(result)
warning_colors = ["black", "red", "white", "gray"]

for color in warning_colors:
    print(f"Alert: {color} poop needs attention")
    assessment = {
    "color": "brown",
    "consistency": "firm",
    "urgency": "normal",
    "action": "No action needed"
}

print(assessment["color"])
print(assessment.get("urgency", "unknown"))
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
print(f"Key loaded: {api_key[:10]}...")