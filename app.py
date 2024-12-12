import os
import requests
from flask import Flask, request, jsonify
import re

# Initialize Flask app
app = Flask(__name__)

# Your OCR Space API Key
OCR_SPACE_API_KEY = "K82938415388957"

# OCR Space API URL
OCR_SPACE_API_URL = "https://api.ocr.space/parse/image"

# Function to extract text using OCR Space API
def extract_text_from_image(image_url):
    payload = {
        'url': image_url,
        'apikey': OCR_SPACE_API_KEY,
        'language': 'eng',
        'isTable': True
    }
    try:
        response = requests.post(OCR_SPACE_API_URL, data=payload)
        response.raise_for_status()

        result = response.json()
        if result.get("IsErroredOnProcessing"):
            return {"error": result.get("ErrorMessage", "Unknown error")}
        return {"text": result.get("ParsedResults")[0].get("ParsedText", "")}
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# Function to parse NPK and OC values from extracted text
def parse_soil_health_card(text):
    try:
        # Look for patterns for NPK and OC values
        data = {
            "Nitrogen": None,
            "Phosphorus": None,
            "Potassium": None,
            "Organic Carbon": None
        }
        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if 'organic carbon' in line_lower:
                data['Organic Carbon'] = extract_numeric_value(line)
            elif 'nitrogen' in line_lower:
                data['Nitrogen'] = extract_numeric_value(line)
            elif 'phosphorus' in line_lower or 'phosphates' in line_lower:
                data['Phosphorus'] = extract_numeric_value(line)
            elif 'potassium' in line_lower:
                data['Potassium'] = extract_numeric_value(line)
            
        return data
    except Exception as e:
        return {"error": str(e)}

# Helper function to extract numeric value from a line and handle missing decimals
def extract_numeric_value(line):
    # Search for numeric values in the line
    match = re.search(r'\d+(\.\d+)?', line)
    if match:
        value = match.group()
        # If the value doesn't have a decimal, add '.00' and convert it to float
        if '.' not in value:
            value = str(float(value) / 100)  # Assuming the number needs to be divided by 100 (for values like 3600 to 36.00)
        return round(float(value), 2)
    return None

# API endpoint to process soil health card
@app.route('/extract_soil_health_card', methods=['POST'])
def extract_soil_health_card():
    try:
        data = request.json
        image_url = data.get("image_url")
        if not image_url:
            return jsonify({"error": "No image URL provided."}), 400

        # Extract text using OCR
        ocr_result = extract_text_from_image(image_url)
        if "error" in ocr_result:
            return jsonify({"error": ocr_result["error"]}), 400

        # Parse NPK and OC values from extracted text
        parsed_data = parse_soil_health_card(ocr_result["text"])
        return jsonify({"success": True, "data": parsed_data})

    except Exception as e:
        return jsonify({"error": f"Unexpected error occurred: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
