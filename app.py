import os
import tempfile
import math
from urllib.parse import quote_plus
import httpx
from flask import Flask, request, jsonify, render_template
from analyzer import analyze

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

DISCLOSURE_VERSION = "2026-06-23"

@app.route("/")
def home():
    return render_template("index.html", disclosure_version=DISCLOSURE_VERSION)

@app.route("/analyze", methods=["POST"])
def analyze_route():
    accepted = request.form.get("disclosure_accepted") == "true"
    version = request.form.get("disclosure_version")
    if not accepted or version != DISCLOSURE_VERSION:
        return jsonify({
            "error": "Please confirm that you understand the PoopSense safety notice before requesting an analysis."
        }), 400

    if "photo" not in request.files:
        return jsonify({"error": "No photo uploaded"}), 400

    photo = request.files["photo"]
    if not photo.filename:
        return jsonify({"error": "Please select a photo first"}), 400
    if not (photo.mimetype or "").startswith("image/"):
        return jsonify({"error": "The uploaded file must be an image"}), 400

    suffix = os.path.splitext(photo.filename)[1].lower() or ".jpg"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            photo.save(temp_file.name)
            temp_path = temp_file.name

        result = analyze(temp_path)
        result["disclaimer"] = (
            "Informational visual screening only. PoopSense is not a veterinarian, "
            "does not diagnose disease, and cannot replace an examination or testing."
        )
        result["disclosure_version"] = DISCLOSURE_VERSION
        return jsonify(result)
    except Exception:
        app.logger.exception("PoopSense analysis failed")
        return jsonify({
            "error": "The image could not be analyzed right now. Please try another clear photo or contact your veterinarian."
        }), 502
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "The image is too large. Please upload a photo under 10 MB."}), 413


@app.route("/vets")
def nearby_vets():
    try:
        latitude = float(request.args.get("lat", ""))
        longitude = float(request.args.get("lng", ""))
    except ValueError:
        return jsonify({"error": "A valid location is required."}), 400

    if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
        return jsonify({"error": "A valid location is required."}), 400

    query = f"""
    [out:json][timeout:20];
    (
      nwr["amenity"="veterinary"](around:50000,{latitude},{longitude});
      nwr["healthcare"="veterinary"](around:50000,{latitude},{longitude});
    );
    out center tags;
    """

    try:
        response = httpx.post(
            "https://overpass-api.de/api/interpreter",
            content=query,
            headers={"User-Agent": "PoopSense/1.0 veterinary-finder"},
            timeout=25,
        )
        response.raise_for_status()
        elements = response.json().get("elements", [])
    except (httpx.HTTPError, ValueError):
        app.logger.exception("Veterinary location lookup failed")
        return jsonify({
            "error": "Nearby clinic listings are temporarily unavailable. Use the emergency map search below.",
            "emergency_search_url": emergency_search_url(latitude, longitude),
        }), 502

    clinics = []
    seen = set()
    for element in elements:
        tags = element.get("tags", {})
        name = tags.get("name")
        clinic_lat = element.get("lat") or element.get("center", {}).get("lat")
        clinic_lng = element.get("lon") or element.get("center", {}).get("lon")
        if not name or clinic_lat is None or clinic_lng is None:
            continue

        identity = (name.lower(), round(clinic_lat, 4), round(clinic_lng, 4))
        if identity in seen:
            continue
        seen.add(identity)

        hours = tags.get("opening_hours", "")
        emergency = (
            hours.strip().lower() == "24/7"
            or tags.get("emergency") == "yes"
            or "emergency" in name.lower()
            or "24 hour" in name.lower()
            or "24-hour" in name.lower()
        )
        address = format_address(tags)
        phone = tags.get("phone") or tags.get("contact:phone") or ""
        query_text = ", ".join(part for part in (name, address) if part)
        clinics.append({
            "name": name,
            "address": address or "Address available in maps",
            "phone": phone,
            "hours": hours or "Hours not listed",
            "website": tags.get("website") or tags.get("contact:website") or "",
            "distance_miles": round(distance_miles(latitude, longitude, clinic_lat, clinic_lng), 1),
            "latitude": clinic_lat,
            "longitude": clinic_lng,
            "is_24_hour": hours.strip().lower() == "24/7",
            "is_emergency": emergency,
            "maps_url": f"https://www.google.com/maps/search/?api=1&query={quote_plus(query_text)}",
            "navigate_url": (
                "https://www.google.com/maps/dir/?api=1"
                f"&destination={clinic_lat}%2C{clinic_lng}&travelmode=driving&dir_action=navigate"
            ),
        })

    clinics.sort(key=lambda clinic: clinic["distance_miles"])
    verified_emergency = next((clinic for clinic in clinics if clinic["is_24_hour"]), None)
    selected = ([verified_emergency] if verified_emergency else []) + clinics[:10]
    clinics = list({(clinic["name"], clinic["latitude"], clinic["longitude"]): clinic for clinic in selected}.values())
    return jsonify({
        "clinics": clinics,
        "emergency_search_url": emergency_search_url(latitude, longitude),
        "source_note": (
            "Clinic details come from public map listings and may be incomplete. "
            "Open Maps to see current ratings and call to confirm hours before traveling."
        ),
    })


def format_address(tags):
    street = " ".join(filter(None, (tags.get("addr:housenumber"), tags.get("addr:street"))))
    locality = ", ".join(filter(None, (tags.get("addr:city"), tags.get("addr:state"), tags.get("addr:postcode"))))
    return ", ".join(filter(None, (street, locality)))


def distance_miles(lat1, lng1, lat2, lng2):
    radius_miles = 3958.8
    lat_delta = math.radians(lat2 - lat1)
    lng_delta = math.radians(lng2 - lng1)
    a = (
        math.sin(lat_delta / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(lng_delta / 2) ** 2
    )
    return radius_miles * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def emergency_search_url(latitude, longitude):
    return (
        "https://www.google.com/maps/search/?api=1&query="
        f"{quote_plus(f'24 hour emergency veterinarian near {latitude},{longitude}')}"
    )

port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)
