import os
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

endpoint = os.getenv("ENDPOINT")  # Foundry project endpoint
model_deployment = os.getenv("MODEL_DEPLOYMENT")  # dall-e-3
api_key = os.getenv("AZURE_OPENAI_API_KEY")       # Foundry project key

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_image():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
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

        # Foundry responses vary — check common paths
        image_url = (
            result.get("outputs", {}).get("image_url") or
            result.get("outputs", {}).get("images", [{}])[0].get("url") or
            result.get("data", [{}])[0].get("url")
        )

        if not image_url:
            return jsonify({"error": "No image URL returned", "raw_response": result}), 500

        return jsonify({"image_url": image_url})

    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

if __name__ == "__main__":
    app.run(debug=True)