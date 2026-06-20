from flask import Blueprint, request, jsonify

voice_routes = Blueprint("voice_routes", __name__)

@voice_routes.route("/voice", methods=["POST"])
def process_voice():

    data = request.json
    text = data.get("text")

    if not text:
        return jsonify({"error": "No voice text provided"}), 400

    response = f"Voice received: {text}"

    return jsonify({
        "voice_text": text,
        "response": response
    })