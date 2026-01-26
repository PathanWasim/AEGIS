"""
Parser module for AEGIS - Builds Abstract Syntax Trees from tokens.
"""

from .parser import Parser
from ..errors import SyntaxError as AegisSyntaxError

# Alias for backward compatibility
ParseError = AegisSyntaxError

__all__ = ['Parser', 'ParseError', 'AegisSyntaxError']