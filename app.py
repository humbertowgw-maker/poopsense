import os
import tempfile
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

port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)
