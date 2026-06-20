from flask import Blueprint, request, jsonify
import os

from backend.services.ai_engine import process_pdf
upload_routes = Blueprint("upload_routes", __name__)

UPLOAD_FOLDER = "uploads"


@upload_routes.route("/upload", methods=["POST"])
def upload_pdf():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)

    file.save(file_path)

    process_pdf(file_path)

    return jsonify({
        "message": "PDF uploaded and processed successfully"
    })