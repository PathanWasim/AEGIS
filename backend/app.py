"""
AEGIS Backend — app.py
Flask entry point: registers blueprints, serves frontend build.
"""

import sys
import os
from pathlib import Path
from flask import Flask, send_from_directory, jsonify

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    from flask_cors import CORS
except ImportError:
    print("Run: pip install flask flask-cors")
    sys.exit(1)

from routes.execute  import execute_bp
from routes.tokenize import tokenize_bp
from routes.analyze  import analyze_bp
from routes.health   import health_bp

FRONTEND_DIST = ROOT / "frontend" / "dist"

app = Flask(__name__, static_folder=str(FRONTEND_DIST), static_url_path="")
CORS(app)

app.register_blueprint(execute_bp,  url_prefix="/api")
app.register_blueprint(tokenize_bp, url_prefix="/api")
app.register_blueprint(analyze_bp,  url_prefix="/api")
app.register_blueprint(health_bp,   url_prefix="/api")


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    """Serve React SPA — fall back to index.html for client-side routing."""
    full = FRONTEND_DIST / path
    if path and full.exists():
        return send_from_directory(str(FRONTEND_DIST), path)
    return send_from_directory(str(FRONTEND_DIST), "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("AEGIS_PORT", 5000))
    print(f"\n{'='*50}")
    print(f"  AEGIS  |  http://localhost:{port}")
    print(f"  React dev: cd frontend && npm run dev")
    print(f"{'='*50}\n")
    app.run(debug=True, port=port, host="0.0.0.0")
