# PoopSense

AI-assisted visual stool screening for pet owners.

PoopSense also supports non-diagnostic dog and cat skin/coat photo screening.
Choose **Skin issue** on the homepage, or send `analysis_type=skin` as multipart
form data or a query parameter. Existing clients remain stool-first because an
omitted or blank `analysis_type` defaults to `stool`.

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

## Engineering Notes

### Keeping the AI safety-bounded

The vision model is treated as an untrusted, non-diagnostic sensor rather than
an authority. That shows up as concrete constraints, not a disclaimer bolted
on afterward:

- **Forced output shape.** `prompt.py` sends Claude a fixed JSON schema (dog,
  cat, stool, and skin variants) instead of free text, so findings like
  `blood_visible` or `parasite_like_material` can only ever be
  `none / possible / unclear` — never a diagnosis. The prompts explicitly
  instruct the model to "remain strictly visual and non-diagnostic," never
  prescribe treatment, and never claim a photo rules out disease.
- **Escalation is a first-class field.** Every response includes a required
  `urgency` value (`normal/monitor/vet_soon/emergency`) with `urgency_reasons`,
  and the prompt tells the model to escalate on possible black/tarry stool,
  substantial blood, foreign objects, or signs of toxin exposure — pointing
  the user to the built-in vet finder rather than a generic "consult a
  professional" line.
- **The app doesn't trust the model's output format either.** `analyzer.py`
  strips Markdown fences, scans for the first valid JSON object in whatever
  Claude returns, and merges it into a `REQUIRED_DEFAULTS` shape so a
  malformed or partial response can't crash the route or silently drop
  fields the frontend expects.
- **Fail closed, not silent.** If the Claude call throws or returns unusable
  JSON, `analyze()` never propagates the exception to the user — it returns a
  `fallback_result()` with `analysis_unavailable: true` and a recommendation
  to try again or contact a vet, instead of guessing.
- **Consent is enforced server-side.** `/analyze` rejects the request with a
  400 unless `disclosure_accepted=true` and a matching `disclosure_version`
  are present in the form data — the safety notice isn't just UI copy, it's
  a gate the backend checks on every call.

### Real debugging, not just feature commits

The commit history has the usual signs of an app that actually got run in
production and broke in normal ways:

- `e641bda` — Railway was booting the app before Alembic ran, so the
  `pet_type` migration never applied on deploy; fixed by chaining
  `alembic upgrade head && python app.py` in the `Procfile`.
- `126acfb` — hardened image handling after the fact: added Pillow's
  decompression-bomb guard (`Image.MAX_IMAGE_PIXELS`), tightened the accepted
  MIME/extension whitelist, added per-IP rate limiting on `/analyze`, added
  security response headers (CSP, `X-Frame-Options`, etc.), added
  `pip-audit` to CI, and deleted committed `__pycache__` artifacts.
- `351d446` — removed leftover scratch files (`basics.py`, `config.py`) that
  printed the first characters of `ANTHROPIC_API_KEY` to stdout — a real
  "don't ship debug prints with secrets in them" cleanup, not a hypothetical.

### What's actually deployed

- Live on Railway at the URL above (Flask + Gunicorn-free `app.run`, backed
  by Postgres in production via `DATABASE_URL`, SQLite locally).
- CI (`.github/workflows/tests.yml`) runs `alembic upgrade head` against a
  fresh SQLite DB and then the full `unittest` suite — 20 tests covering
  consent enforcement, dog/cat prompt selection, skin vs. stool routing,
  pet-type validation, backward-compatible migration of pre-existing rows,
  and the vet finder — on every push. All 20 pass locally as of this
  writing. A separate `security.yml` workflow runs `pip-audit` weekly plus
  on every push to `main`.
- The `/vets` endpoint queries OpenStreetMap's Overpass API live for nearby
  clinics, flags 24/7 locations as emergency options, and falls back to a
  Google Maps search link if Overpass is unreachable — no vet database to
  maintain, no stored user location.
- `/portfolio-metrics` reports only aggregate weekly counts
  (`completed_screenings`, `vet_searches`) from a separate local SQLite file
  — no images, no location, no per-user data retained, which is enforced by
  what the table schema does and doesn't store, not just a stated policy.
- Installable as a PWA (`manifest.webmanifest`, service worker, on-device
  screening history) as of `7cf46e0`.

## Built by
Humberto Zepeda — built in 1 day (base app); safety hardening, multi-pet
support, skin screening, and PWA support added in subsequent sessions.
