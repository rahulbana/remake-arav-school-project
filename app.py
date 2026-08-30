import os
from flask import Flask, render_template

# Initialize Flask application
app = Flask(__name__, static_folder='assets')
# Basic configuration
app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY", "default-dev-secret-key-change-in-prod"
)


@app.route("/", methods=["GET"])
def home():
    """Renders the lifestyle coach landing page."""
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health_check():
    """Basic health check endpoint for monitoring."""
    return {"status": "healthy", "service": "lifestyle-portal"}, 200


if __name__ == "__main__":
    # Development server configuration
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    app.run(host="0.0.0.0", port=port, debug=debug)