"""GET /api/health  |  POST /api/trust/reset  |  GET /api/examples"""

from flask import Blueprint, jsonify
from core.pipeline import reset_all_trust, all_trust_entries
from core.helpers import EXAMPLES

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "version": "2.0.0",
                    "trust_entries": all_trust_entries()})


@health_bp.route("/trust/reset", methods=["POST"])
def trust_reset():
    reset_all_trust()
    return jsonify({"success": True, "message": "Trust scores cleared"})


@health_bp.route("/examples", methods=["GET"])
def examples():
    return jsonify({
        "examples": [
            {"id": k, "name": v["name"], "description": v["description"], "code": v["code"]}
            for k, v in EXAMPLES.items()
        ]
    })
