"""
AEGIS Web Dashboard - Flask API Server

Exposes the AEGIS execution pipeline as a REST API so the web frontend
can run AEGIS programs interactively and display real-time results.

Endpoints:
    POST /api/execute   – run an AEGIS program, return full result
    POST /api/tokenize  – lex only, return token stream
    POST /api/trust     – get trust report for a code hash
    GET  /api/examples  – list built-in example programs
    GET  /api/health    – health check
"""

import json
import hashlib
import os
import sys
import tempfile
import time
import traceback
from pathlib import Path

# ── Flask (install with: pip install flask flask-cors) ──────────────────────
try:
    from flask import Flask, request, jsonify, send_from_directory
    from flask_cors import CORS
except ImportError:
    print("ERROR: Flask not installed.")
    print("Please run:  pip install flask flask-cors")
    sys.exit(1)

# ── AEGIS pipeline ──────────────────────────────────────────────────────────
# Add project root to path so we can import aegis directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from aegis.pipeline import AegisExecutionPipeline
from aegis.lexer import Lexer
from aegis.lexer.tokens import TokenType

# ── App setup ───────────────────────────────────────────────────────────────
app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

# Use a temp file for trusted trust database during web sessions
TRUST_FILE = os.path.join(tempfile.gettempdir(), "aegis_web_trust.json")
pipeline = AegisExecutionPipeline(trust_file=TRUST_FILE, trust_threshold=0.0)
lexer = Lexer()

# ── Example programs ─────────────────────────────────────────────────────────
EXAMPLES = {
    "hello_world": {
        "name": "Hello World",
        "description": "Basic variable assignment and print",
        "code": "x = 42\nprint x",
    },
    "arithmetic": {
        "name": "Arithmetic",
        "description": "All arithmetic operators",
        "code": (
            "a = 10\n"
            "b = 3\n"
            "sum_val = a + b\n"
            "diff = a - b\n"
            "product = a * b\n"
            "quotient = a / b\n"
            "remainder = a % b\n"
            "print sum_val\n"
            "print diff\n"
            "print product\n"
            "print quotient\n"
            "print remainder"
        ),
    },
    "if_else": {
        "name": "If / Else",
        "description": "Conditional branching with comparisons",
        "code": (
            "x = 15\n"
            "y = 10\n"
            "if x > y\n"
            "  result = x\n"
            "else\n"
            "  result = y\n"
            "end\n"
            "print result"
        ),
    },
    "while_loop": {
        "name": "While Loop",
        "description": "Iterative computation",
        "code": (
            "total = 0\n"
            "i = 1\n"
            "while i <= 10\n"
            "  total = total + i\n"
            "  i = i + 1\n"
            "end\n"
            "print total"
        ),
    },
    "fibonacci": {
        "name": "Fibonacci",
        "description": "First 10 Fibonacci numbers",
        "code": (
            "a = 0\n"
            "b = 1\n"
            "count = 0\n"
            "while count < 10\n"
            "  print a\n"
            "  temp = a + b\n"
            "  a = b\n"
            "  b = temp\n"
            "  count = count + 1\n"
            "end"
        ),
    },
    "security_demo": {
        "name": "Trust Builder",
        "description": "Run multiple times to build trust and unlock optimizations",
        "code": (
            "# Safe program - run repeatedly to build trust\n"
            "x = 100\n"
            "y = 200\n"
            "total = x + y\n"
            "print total"
        ),
    },
    "division_by_zero": {
        "name": "Security Violation",
        "description": "Division by zero — triggers security analysis",
        "code": (
            "x = 10\n"
            "y = 0\n"
            "result = x / y\n"
            "print result"
        ),
    },
}


# ── Helper functions ─────────────────────────────────────────────────────────

def token_to_dict(token) -> dict:
    """Convert a Token to a JSON-serialisable dict."""
    return {
        "type": token.type.name,
        "value": token.value,
        "line": token.line,
        "column": token.column,
        "category": _token_category(token.type),
    }


def _token_category(token_type: TokenType) -> str:
    """Group token types for colour-coding in the frontend."""
    keywords   = {TokenType.PRINT, TokenType.IF, TokenType.ELSE, TokenType.WHILE, TokenType.END}
    operators  = {TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE,
                  TokenType.MODULO, TokenType.EQ, TokenType.NEQ, TokenType.LT, TokenType.LTE,
                  TokenType.GT, TokenType.GTE, TokenType.ASSIGN}
    literals   = {TokenType.INTEGER}
    identifiers = {TokenType.IDENTIFIER}
    structural = {TokenType.LPAREN, TokenType.RPAREN, TokenType.NEWLINE, TokenType.EOF}
    if token_type in keywords:    return "keyword"
    if token_type in operators:   return "operator"
    if token_type in literals:    return "literal"
    if token_type in identifiers: return "identifier"
    return "structural"


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the dashboard."""
    return send_from_directory(".", "index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


@app.route("/api/examples")
def get_examples():
    return jsonify({
        "examples": [
            {"id": id_, "name": ex["name"], "description": ex["description"]}
            for id_, ex in EXAMPLES.items()
        ]
    })


@app.route("/api/examples/<example_id>")
def get_example(example_id):
    if example_id not in EXAMPLES:
        return jsonify({"error": "Example not found"}), 404
    ex = EXAMPLES[example_id]
    return jsonify({"id": example_id, "name": ex["name"], "code": ex["code"]})


@app.route("/api/tokenize", methods=["POST"])
def tokenize():
    """Lex source code and return the token stream."""
    data = request.get_json(force=True)
    source = data.get("code", "")
    try:
        tokens = lexer.tokenize(source)
        return jsonify({
            "success": True,
            "tokens": [token_to_dict(t) for t in tokens],
            "token_count": len(tokens),
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 200


@app.route("/api/execute", methods=["POST"])
def execute():
    """Execute AEGIS source code through the full pipeline."""
    data = request.get_json(force=True)
    source = data.get("code", "")
    verbose = data.get("verbose", False)

    if not source.strip():
        return jsonify({"success": False, "error": "No source code provided"}), 400

    start = time.perf_counter()
    try:
        result = pipeline.execute(source, verbose=verbose)
        elapsed = time.perf_counter() - start

        # Build token info
        try:
            tokens = lexer.tokenize(source)
            token_data = [token_to_dict(t) for t in tokens]
        except Exception:
            token_data = []

        # Compute basic trust info
        code_hash = hashlib.sha256(source.encode()).hexdigest()[:8]

        return jsonify({
            "success": result.success,
            "output": result.output if result.output else [],
            "error": result.error_message,
            "trust_score": round(getattr(result, "trust_score", 0.0), 3),
            "execution_time_ms": round(elapsed * 1000, 2),
            "tokens": token_data,
            "optimized": getattr(result, "optimization_applied", False),
            "code_hash": code_hash,
            "pipeline_stages": {
                "lexed":    True,
                "parsed":   result.success or "Syntax" not in (result.error_message or ""),
                "analyzed": result.success or "Semantic" not in (result.error_message or ""),
                "executed": result.success,
            },
        })
    except Exception as e:
        elapsed = time.perf_counter() - start
        return jsonify({
            "success": False,
            "error": f"Internal error: {str(e)}",
            "execution_time_ms": round(elapsed * 1000, 2),
        }), 200


@app.route("/api/trust/reset", methods=["POST"])
def reset_trust():
    """Reset all trust scores (for demo purposes)."""
    global pipeline
    if os.path.exists(TRUST_FILE):
        os.remove(TRUST_FILE)
    pipeline = AegisExecutionPipeline(trust_file=TRUST_FILE, trust_threshold=0.0)
    return jsonify({"success": True, "message": "Trust scores reset"})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("AEGIS_PORT", 5000))
    print(f"\n{'='*55}")
    print(f"  AEGIS Web Dashboard  |  http://localhost:{port}")
    print(f"{'='*55}\n")
    app.run(debug=True, port=port, host="0.0.0.0")
