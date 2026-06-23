import os
from flask import Flask, request, jsonify, render_template
from analyzer import analyze

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze_route():
    if "photo" not in request.files:
        return jsonify({"error": "No photo uploaded"}), 400
    
    photo = request.files["photo"]
    photo.save("temp_upload.jpg")
    
    result = analyze("temp_upload.jpg")
    return jsonify(result)

port = int(os.environ.get("PORT", 5000))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=port, debug=False)