# === Imports ===
import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

# === Flask App Setup ===
app = Flask(__name__)

# === Load environment variables from .env ===
load_dotenv()
endpoint = os.getenv("ENDPOINT")  # Foundry project endpoint
model_deployment = os.getenv("MODEL_DEPLOYMENT")  # dall-e-3
api_key = os.getenv("FOUNDRY_API_KEY")            # Foundry project key

# === Home Route (for browser UI) ===
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# === Image Generation Route (Foundry infer style) ===
@app.route("/generate", methods=["POST"])
def generate_image():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        # Foundry infer endpoint
        url = f"{endpoint}/infer"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "inputs": { "prompt": prompt },
            "deployment": model_deployment
        }

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        # Try to extract image URL from common response shapes
        image_url = None
        if "outputs" in result:
            if isinstance(result["outputs"], dict):
                image_url = result["outputs"].get("image_url")
                if not image_url and "images" in result["outputs"]:
                    image_url = result["outputs"]["images"][0].get("url")
            elif isinstance(result["outputs"], list):
                image_url = result["outputs"][0].get("url")
        elif "data" in result:
            image_url = result["data"][0].get("url")

        if not image_url:
            return jsonify({
                "error": "No image URL returned",
                "raw_response": result
            }), 500

        return jsonify({"image_url": image_url})

    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

# === Run Locally (ignored by Render) ===
if __name__ == "__main__":
    app.run(debug=True)