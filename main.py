from flask import Flask, jsonify, request
import requests
import os
import json
import gspread

app = Flask(__name__)

@app.route("/")
def home():
    return "DukaanOS API is running!"

def fetch_product(barcode):
    url = f"https://world.openfoodfacts.org/api/v3/product/{barcode}.json"

    response = requests.get(
        url,
        headers={"User-Agent": "DukaanOS/1.0"},
        timeout=25
    )

    data = response.json()
    product = data.get("product") or {}

    return {
        "found": bool(
            data.get("status") in (1, "1", "success")
            or product.get("product_name")
        ),
        "barcode": barcode,
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
        return jsonify({"error": str(e)}), 500

@app.route("/lookup-and-update", methods=["POST"])
def lookup_and_update():
    try:
        barcode = str(request.json.get("barcode", "")).strip()

        if not barcode:
            return jsonify({"error": "Barcode missing"}), 400

        product = fetch_product(barcode)

        if not product["found"]:
            return jsonify({
                "success": False,
                "message": "Product not found",
                "barcode": barcode
            })

        credentials = json.loads(
            os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"]
        )

        client = gspread.service_account_from_dict(credentials)

        spreadsheet = client.open_by_key(
            os.environ["SPREADSHEET_ID"]
        )

        sheet = spreadsheet.worksheet("Sheet1")

        barcodes = sheet.col_values(1)

        if barcode not in barcodes:
            return jsonify({"error": "Barcode row not found"}), 404

        row = barcodes.index(barcode) + 1

        current = sheet.row_values(row)

        name = product.get("name") or (current[1] if len(current) > 1 else "")
        brand = product.get("brand") or (current[2] if len(current) > 2 else "")
        quantity = product.get("quantity") or (current[3] if len(current) > 3 else "")
        image = product.get("image") or (current[7] if len(current) > 7 else "")

        sheet.update(
            range_name=f"B{row}:D{row}",
            values=[[name, brand, quantity]]
        )

        sheet.update(
            range_name=f"H{row}",
            values=[[image]]
        )

        return jsonify({
            "success": True,
            "message": "Product updated",
            "barcode": barcode,
            "name": name,
            "brand": brand,
            "quantity": quantity
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
