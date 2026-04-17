"""POST /api/analyze — static analysis only"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from flask import Blueprint, request, jsonify
from aegis.lexer.lexer import Lexer
from aegis.parser.parser import Parser
from aegis.errors import LexicalError, SyntaxError as AegisSyntaxError
from core.pipeline import run_static_analysis

analyze_bp = Blueprint("analyze", __name__)
_lexer  = Lexer()
_parser = Parser()


@analyze_bp.route("/analyze", methods=["POST"])
def analyze():
    data   = request.get_json(force=True) or {}
    source = data.get("code", "").strip()
    if not source:
        return jsonify({"success": False, "error": "No code provided"}), 400
    try:
        tokens    = _lexer.tokenize(source)
        ast_nodes = _parser.parse(tokens)
    except (LexicalError, AegisSyntaxError) as e:
        return jsonify({"success": False, "error": str(e), "issues": []})

    issues   = run_static_analysis(ast_nodes)
    has_high = any(i.severity == "HIGH" for i in issues)
    return jsonify({
        "success":              True,
        "issues":               [i.to_dict() for i in issues],
        "issue_count":          len(issues),
        "optimization_blocked": has_high,
        "clean":                len(issues) == 0,
    })
