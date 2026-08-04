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
```bash
git clone https://github.com/humbertowgw-maker/poopsense.git
cd poopsense
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python app.py
```

## Multi-Pet Support

PoopSense supports dog and cat stool screening. Select the pet type before
uploading a photo; the selection is sent as multipart `pet_type` and chooses a
species-specific Claude Vision prompt. API clients may instead use
`POST /analyze?pet_type=dog` or `pet_type=cat`. Multipart form data takes
precedence, invalid values return HTTP 400, and omitted or blank values default
to `dog` for backward compatibility.

Analysis records use the same configured SQLite or PostgreSQL database. Run
`alembic upgrade head` after deployment to add the `pet_type` enum and the
`(pet_type, created_at)` index. Existing records are automatically marked as
`dog`. Claude responses wrapped in Markdown or surrounding prose are parsed,
normalized to a stable result shape, and replaced with a safe generic fallback
if the vision service or JSON response is unavailable.

## Built by
Humberto Zepeda — built in 1 day
