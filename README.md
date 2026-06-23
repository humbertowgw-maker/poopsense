# PoopSense

AI-assisted visual stool screening for pet owners.

PoopSense is an informational tool, not a veterinarian. It does not diagnose
illness and should not replace veterinary examination, fecal testing, treatment,
or emergency care. The web app requires users to acknowledge this notice before
requesting an analysis.

The app also includes a location-based veterinary finder with public listing
hours and phone data, a 24-hour emergency-care priority, direct calling, and
Google Maps navigation. Location is requested only when the user starts a search
and is not stored by PoopSense.

**Live Demo:** https://web-production-fb2d1.up.railway.app

## Tech Stack
- Python 3.14
- Flask
- Anthropic Claude Vision API
- Railway

## How to run locally
git clone https://github.com/humbertowgw-maker/poopsense.git
cd poopsense
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py

## Built by
Humberto Zepeda — built in 1 day
