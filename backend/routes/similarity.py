from flask import Blueprint, request, jsonify
from services.similarity_model import calculate_similarity

similarity_routes = Blueprint("similarity_routes", __name__)


@similarity_routes.route("/similarity", methods=["POST"])
def check_similarity():

    data = request.json

    text1 = data.get("text1")
    text2 = data.get("text2")

    if not text1 or not text2:
        return jsonify({"error": "Both texts required"}), 400

    score = calculate_similarity(text1, text2)

    return jsonify({
        "text1": text1,
        "text2": text2,
        "similarity_score": score
    })