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
    "edge_div_zero": {
        "name": "Edge: Div By Zero",
        "description": "Static Analyzer catches division by zero",
        "code": "x = 10\ny = 0\nresult = x / y\nprint result",
    },
    "edge_undef_var": {
        "name": "Edge: Undefined Var",
        "description": "Static Analyzer catches uninitialized variables",
        "code": "x = 10\nprint y",
    },
    "edge_static_loop": {
        "name": "Edge: Infinite Loop (Static)",
        "description": "Static Analyzer flags deterministic infinite loop",
        "code": "count = 0\nwhile 1 == 1\n  count = count + 1\n  print count\nend",
    },
    "edge_overflow": {
        "name": "Edge: Memory Limit/Overflow",
        "description": "Static Analyzer warns of 32-bit bound overflow",
        "code": "x = 99999999999999999\nprint x * x",
    },
    "edge_deep_nesting": {
        "name": "Edge: Deep Nesting",
        "description": "Static Analyzer prevents stack exhaustion",
        "code": "if 1 == 1\n  if 2 == 2\n    if 3 == 3\n      if 4 == 4\n        print 5\n      end\n    end\n  end\nend",
    },
    "edge_inst_limit": {
        "name": "Edge: Instruction Limit",
        "description": "Runtime Monitor halts loop exceeding 1000 ops",
        "code": "x = 0\n# The condition is valid, but the loop takes too long\nwhile x < 5000\n  x = x + 1\nend\nprint x",
    },
}
