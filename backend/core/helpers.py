"""
backend/core/helpers.py
Shared helpers: token categorization, examples dict.
"""

from aegis.lexer.tokens import TokenType

# ── Token category mapping ────────────────────────────────────────────────────

_KEYWORDS    = {TokenType.PRINT, TokenType.IF, TokenType.ELSE, TokenType.WHILE, TokenType.END}
_OPERATORS   = {TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE,
                TokenType.MODULO, TokenType.EQ, TokenType.NEQ, TokenType.LT,
                TokenType.LTE, TokenType.GT, TokenType.GTE, TokenType.ASSIGN}
_LITERALS    = {TokenType.INTEGER}
_IDENTIFIERS = {TokenType.IDENTIFIER}


def token_category(token_type: TokenType) -> str:
    if token_type in _KEYWORDS:    return "keyword"
    if token_type in _OPERATORS:   return "operator"
    if token_type in _LITERALS:    return "literal"
    if token_type in _IDENTIFIERS: return "identifier"
    return "structural"


def token_to_dict(token) -> dict:
    return {
        "type":     token.type.name,
        "value":    token.value,
        "line":     token.line,
        "column":   token.column,
        "category": token_category(token.type),
    }


# ── Built-in examples ─────────────────────────────────────────────────────────

EXAMPLES = {
    "hello_world": {
        "name": "Hello World",
        "description": "Basic variable and print",
        "code": "x = 42\nprint x",
    },
    "arithmetic": {
        "name": "Arithmetic",
        "description": "All operators: + - * / %",
        "code": "a = 10\nb = 3\nprint a + b\nprint a - b\nprint a * b\nprint a / b\nprint a % b",
    },
    "if_else": {
        "name": "If / Else",
        "description": "Conditional branching",
        "code": "x = 15\ny = 10\nif x > y\n  result = x\nelse\n  result = y\nend\nprint result",
    },
    "while_loop": {
        "name": "While Loop",
        "description": "Sum 1 to 10",
        "code": "total = 0\ni = 1\nwhile i <= 10\n  total = total + i\n  i = i + 1\nend\nprint total",
    },
    "fibonacci": {
        "name": "Fibonacci",
        "description": "First 10 Fibonacci numbers",
        "code": "a = 0\nb = 1\ncount = 0\nwhile count < 10\n  print a\n  temp = a + b\n  a = b\n  b = temp\n  count = count + 1\nend",
    },
    "trust_demo": {
        "name": "Trust Builder",
        "description": "Run repeatedly: Interpreter → Optimized",
        "code": "# Run this multiple times to build trust\nx = 100\ny = 200\ntotal = x + y\nprint total",
    },
    "security_violation": {
        "name": "Security Violation",
        "description": "Division by zero — triggers rollback",
        "code": "x = 10\ny = 0\nresult = x / y\nprint result",
    },
    "comparison": {
        "name": "Comparisons",
        "description": "All comparison operators",
        "code": "a = 5\nb = 10\nprint a == b\nprint a != b\nprint a < b\nprint a <= b\nprint a > b\nprint a >= b",
    },
}
