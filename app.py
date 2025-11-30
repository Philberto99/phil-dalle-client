# === Imports ===
import os
import json
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI

# === Flask App Setup ===
app = Flask(__name__)

# === Load environment variables from .env ===
load_dotenv()
endpoint = os.getenv("ENDPOINT")
model_deployment = os.getenv("MODEL_DEPLOYMENT")
api_version = os.getenv("API_VERSION")

# === Azure OpenAI Client Setup ===
# Uses DefaultAzureCredential to authenticate via Azure AD
token_provider = get_bearer_token_provider(
    DefaultAzureCredential(
        exclude_environment_credential=True,
        exclude_managed_identity_credential=True
    ),
    "https://cognitiveservices.azure.com/.default"
)

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    azure_ad_token_provider=token_provider
)

# === Home Route ===
@app.route("/", methods=["GET"])
def home():
    return "✅ phil-dalle-client is live and ready to generate images!"

# === Image Generation Route ===
@app.route("/generate", methods=["POST"])
def generate_image():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    try:
        # Call Azure OpenAI to generate image
        result = client.images.generate(
            model=model_deployment,
            prompt=prompt,
            n=1
        )

        # Parse response to extract image URL
        json_response = json.loads(result.model_dump_json())
        image_url = json_response["data"][0]["url"]

        return jsonify({"image_url": image_url})
    except Exception as ex:
        return jsonify({"error": str(ex)}), 500

# === Run Locally (ignored by Render) ===
if __name__ == "__main__":
    app.run(debug=True)