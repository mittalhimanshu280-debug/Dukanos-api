

from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "DukaanOS API is running!"

def fetch_product(barcode):
    url = f"https://world.openfoodfacts.org/api/v3/product/{barcode}.json"

    headers = {
        "User-Agent": "DukaanOS/1.0 (Product Inventory App)"
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=25
    )

    data = response.json()
    product = data.get("product") or {}
    status = data.get("status")

    found = (
        status in (1, "1", "success")
        or bool(product.get("product_name"))
    )

    return {
        "found": found,
        "barcode": barcode,
        "api_status": status,
        "status_verbose": data.get("status_verbose"),
        "name": product.get("product_name"),
        "brand": product.get("brands"),
        "quantity": product.get("quantity"),
        "image": product.get("image_url")
    }

@app.route("/product/<barcode>")
def get_product(barcode):
    try:
        return jsonify(fetch_product(barcode))
    except Exception as e:
        return jsonify({
            "found": False,
            "error": str(e)
        }), 500

@app.route("/debug/<barcode>")
def debug_product(barcode):
    try:
        url = f"https://world.openfoodfacts.org/api/v3/product/{barcode}.json"
        response = requests.get(
            url,
            headers={"User-Agent": "DukaanOS/1.0"},
            timeout=25
        )

        return jsonify({
            "http_status": response.status_code,
            "response": response.json()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
