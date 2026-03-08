"""
Lexer implementation for AEGIS - converts source code into tokens.

This module implements the lexical analysis phase of the AEGIS compiler,
converting source code text into a stream of tokens for parsing.

Supported tokens:
    - Identifiers and keywords (if, else, while, end, print)
    - Integer literals
    - Arithmetic operators: +, -, *, /, %
    - Comparison operators: ==, !=, <, <=, >, >=
    - Assignment: =
    - Parentheses: (, )
    - Comments: # to end of line
"""

from typing import List, Optional
from .tokens import Token, TokenType
from ..errors import LexicalError


class Lexer:
    """
    Lexer for the AEGIS language - converts source code into tokens.

    The lexer performs character-by-character scanning of source code,
    recognizing language constructs and converting them into tokens.
    It maintains position tracking for error reporting.
    """

    def __init__(self):
        """Initialize the lexer."""
        self.source = ""
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def tokenize(self, source_code: str) -> List[Token]:
        """
        Tokenize source code into a list of tokens.

        Args:
            source_code: The AEGIS source code to tokenize

        Returns:
            List of tokens representing the source code

        Raises:
            LexicalError: If invalid characters are encountered
        """
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []

        while not self._is_at_end():
            self._scan_token()

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    # ------------------------------------------------------------------
    # Scanning helpers
    # ------------------------------------------------------------------

    def _scan_token(self) -> None:
        """Scan and create the next token from the current position."""
        char = self._advance()

        # Skip horizontal whitespace
        if char in ' \t\r':
            return

        # Newlines are statement separators
        if char == '\n':
            self._add_token(TokenType.NEWLINE, char)
            self.line += 1
            self.column = 1
            return

        # Comments: skip rest of line
        if char == '#':
            while not self._is_at_end() and self._peek() != '\n':
                self._advance()
            return

        # Two-character tokens first
        if char == '=':
            if self._match_char('='):
                self._add_token(TokenType.EQ, '==')
            else:
                self._add_token(TokenType.ASSIGN, '=')

        elif char == '!':
            if self._match_char('='):
                self._add_token(TokenType.NEQ, '!=')
            else:
                raise LexicalError(
                    f"Unexpected character '!'. Did you mean '!='?",
                    self.line, self.column - 1, char,
                    suggestions=["Use '!=' for not-equal comparison"]
                )

        elif char == '<':
            if self._match_char('='):
                self._add_token(TokenType.LTE, '<=')
            else:
                self._add_token(TokenType.LT, '<')

        elif char == '>':
            if self._match_char('='):
                self._add_token(TokenType.GTE, '>=')
            else:
                self._add_token(TokenType.GT, '>')

        # Arithmetic
        elif char == '+':
            self._add_token(TokenType.PLUS, char)
        elif char == '-':
            self._add_token(TokenType.MINUS, char)
        elif char == '*':
            self._add_token(TokenType.MULTIPLY, char)
        elif char == '/':
            self._add_token(TokenType.DIVIDE, char)
        elif char == '%':
            self._add_token(TokenType.MODULO, char)

        # Grouping
        elif char == '(':
            self._add_token(TokenType.LPAREN, char)
        elif char == ')':
            self._add_token(TokenType.RPAREN, char)

        # Numeric literals
        elif self._is_digit(char):
            self._scan_number()

        # Identifiers and keywords
        elif self._is_alpha(char):
            self._scan_identifier()

        else:
            raise LexicalError(
                f"Unexpected character: '{char}'",
                self.line, self.column - 1, char,
                suggestions=[
                    "Remove or replace the invalid character",
                    "AEGIS only supports letters, digits, and standard operators"
                ]
            )

    def _scan_number(self) -> None:
        """Scan an integer literal."""
        start_pos = self.position - 1
        while not self._is_at_end() and self._is_digit(self._peek()):
            self._advance()
        number_text = self.source[start_pos:self.position]
        self._add_token(TokenType.INTEGER, number_text)

    def _scan_identifier(self) -> None:
        """Scan an identifier or keyword."""
        start_pos = self.position - 1
        while not self._is_at_end() and self._is_alphanumeric(self._peek()):
            self._advance()
        identifier_text = self.source[start_pos:self.position]
        token_type = self._get_keyword_type(identifier_text) or TokenType.IDENTIFIER
        self._add_token(token_type, identifier_text)

    def _get_keyword_type(self, text: str) -> Optional[TokenType]:
        """Return the keyword TokenType for the given text, or None."""
        keywords = {
            'print': TokenType.PRINT,
            'if':    TokenType.IF,
            'else':  TokenType.ELSE,
            'while': TokenType.WHILE,
            'end':   TokenType.END,
        }
        return keywords.get(text)

    # ------------------------------------------------------------------
    # Character utilities
    # ------------------------------------------------------------------

    def _is_digit(self, char: str) -> bool:
        return char.isdigit()

    def _is_alpha(self, char: str) -> bool:
        return char.isalpha() or char == '_'

    def _is_alphanumeric(self, char: str) -> bool:
        return char.isalnum() or char == '_'

    def _is_at_end(self) -> bool:
        return self.position >= len(self.source)

    def _advance(self) -> str:
        """Consume and return the current character."""
        if self._is_at_end():
            return '\0'
        char = self.source[self.position]
        self.position += 1
        self.column += 1
        return char

    def _match_char(self, expected: str) -> bool:
        """Consume the next character only if it matches expected."""
        if self._is_at_end() or self.source[self.position] != expected:
            return False
        self.position += 1
        self.column += 1
        return True

    def _peek(self) -> str:
        """Look at current character without consuming it."""
        if self._is_at_end():
            return '\0'
        return self.source[self.position]

    def _add_token(self, token_type: TokenType, value: str) -> None:
        """Add a token to the tokens list."""
        start_column = self.column - len(value)
        self.tokens.append(Token(token_type, value, self.line, start_column))