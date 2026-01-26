"""
Lexer module for AEGIS - Converts source code into tokens.
"""

from .tokens import Token, TokenType
from .lexer import Lexer
from ..errors import LexicalError

# Alias for backward compatibility
LexerError = LexicalError

__all__ = ['Token', 'TokenType', 'Lexer', 'LexerError', 'LexicalError']