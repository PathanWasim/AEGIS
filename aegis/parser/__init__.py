"""
Parser module for AEGIS - Builds Abstract Syntax Trees from tokens.
"""

from .parser import Parser, ParseError

__all__ = ['Parser', 'ParseError']