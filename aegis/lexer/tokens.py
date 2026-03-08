"""
Token definitions for the AEGIS lexer.

This module defines the token types and Token dataclass used throughout
the lexical analysis phase of the AEGIS system.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    """
    Enumeration of all token types supported by the AEGIS language.
    
    The AEGIS language supports:
    - Variable identifiers
    - Integer literals
    - String literals
    - Assignment operator (=)
    - Arithmetic operators (+, -, *, /)
    - Comparison operators (==, !=, <, <=, >, >=)
    - Parentheses ((, ))
    - Control flow keywords (IF, ELSE, WHILE, END)
    - Print keyword
    - End of file marker
    - Newline for statement separation
    """
    IDENTIFIER = auto()
    INTEGER = auto()
    STRING = auto() # Added string literal type

    # Operators
    ASSIGN = auto()
    PLUS = auto()
    MINUS = auto()
    MULTIPLY = auto()
    DIVIDE = auto()
    EQ = auto()     # ==
    NEQ = auto()    # !=
    LT = auto()     # <
    LTE = auto()    # <=
    GT = auto()     # >
    GTE = auto()    # >=

    # Delimiters
    LPAREN = auto() # (
    RPAREN = auto() # )

    # Keywords
    IF = auto()
    ELSE = auto()
    WHILE = auto()
    END = auto()
    PRINT = auto()

    # Special
    EOF = auto()
    NEWLINE = auto()


@dataclass
class Token:
    """
    Represents a single token in the AEGIS language.
    
    Each token contains:
    - type: The category of token (from TokenType enum)
    - value: The actual text value from source code
    - line: Line number in source code (1-based)
    - column: Column number in source code (1-based)
    
    Position information is crucial for error reporting and debugging.
    """
    type: TokenType
    value: str
    line: int
    column: int
    
    def __str__(self) -> str:
        """String representation for debugging and logging."""
        return f"Token({self.type.name}, '{self.value}', {self.line}:{self.column})"
    
    def __repr__(self) -> str:
        """Detailed representation for debugging."""
        return self.__str__()