import sys
import os
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Load environment variables
load_dotenv()

from flask import Flask
from flask_cors import CORS

# Import routes
from backend.routes.qa import qa_routes
from backend.routes.similarity import similarity_routes
from backend.routes.upload import upload_routes
from backend.routes.voice import voice_routes
from backend.routes.analytics import analytics_routes

app = Flask(__name__)
CORS(app)

# Register APIs
app.register_blueprint(qa_routes)
app.register_blueprint(similarity_routes)
app.register_blueprint(upload_routes)
app.register_blueprint(voice_routes)
app.register_blueprint(analytics_routes)


@app.route("/")
def home():
    return {
        "message": "AI Academic Assistant Backend Running"
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)