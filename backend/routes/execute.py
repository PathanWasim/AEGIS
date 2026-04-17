"""POST /api/execute — full pipeline"""

from flask import Blueprint, request, jsonify
from core.pipeline import run_pipeline

execute_bp = Blueprint("execute", __name__)


@execute_bp.route("/execute", methods=["POST"])
def execute():
    data   = request.get_json(force=True) or {}
    source = data.get("code", "").strip()
    if not source:
        return jsonify({"success": False, "error": "No code provided"}), 400
    return jsonify(run_pipeline(source).to_dict())
