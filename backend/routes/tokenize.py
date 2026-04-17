"""POST /api/tokenize"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from flask import Blueprint, request, jsonify
from aegis.lexer.lexer import Lexer
from aegis.errors import LexicalError
from core.helpers import token_to_dict

tokenize_bp = Blueprint("tokenize", __name__)
_lexer = Lexer()


@tokenize_bp.route("/tokenize", methods=["POST"])
def tokenize():
    data   = request.get_json(force=True) or {}
    source = data.get("code", "")
    try:
        tokens = _lexer.tokenize(source)
        return jsonify({
            "success": True,
            "tokens":  [token_to_dict(t) for t in tokens],
            "count":   len(tokens),
        })
    except LexicalError as e:
        return jsonify({"success": False, "error": str(e)})
