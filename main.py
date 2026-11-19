from flask import Flask, jsonify
import requests

app = Flask(__name__)

@app.route("/")
def home():
    return "DukaanOS API is running!"

@app.route("/product/<barcode>")
def get_product(barcode):
    url = f"https://world.openfoodfacts.org/api/v3/product/{barcode}.json"
    headers = {"User-Agent": "DukaanOS/1.0"}

    try:
        r = requests.get(url, headers=headers, timeout=20)
        r.raise_for_status()
        data = r.json()
        p = data.get("product", {})

        if data.get("status") != 1:
            return jsonify({"found": False})

        return jsonify({
            "found": True,
            "barcode": barcode,
            "name": p.get("product_name"),
            "brand": p.get("brands"),
            "quantity": p.get("quantity"),
            "image": p.get("image_url")
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
