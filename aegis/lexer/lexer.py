"""
Lexer implementation for AEGIS - converts source code into tokens.

This module implements the lexical analysis phase of the AEGIS compiler,
converting source code text into a stream of tokens for parsing.
"""

from typing import List, Optional
from .tokens import Token, TokenType
from ..errors import LexicalError


class Lexer:
    """
    Lexer for the AEGIS language - converts source code into tokens.
    
    The lexer performs character-by-character scanning of source code,
    recognizing language constructs and converting them into tokens.
    It maintains position tracking for error reporting and handles
    whitespace appropriately.
    
    Supported tokens:
    - Identifiers: variable names (letters, digits, underscores)
    - Integers: numeric literals (digits only)
    - Operators: =, +, -, *, /
    - Keywords: print
    - Separators: newlines
    - EOF: end of file marker
    """
    
    def __init__(self):
        """Initialize the lexer."""
        self.source = ""
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
    
    def tokenize(self, source_code: str) -> List[Token]:
        """
        Tokenize source code into a list of tokens.
        
        Args:
            source_code: The AEGIS source code to tokenize
            
        Returns:
            List of tokens representing the source code
            
        Raises:
            LexerError: If invalid characters are encountered
        """
        self.source = source_code
        self.position = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        
        while not self._is_at_end():
            self._scan_token()
        
        # Add EOF token
        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        
        return self.tokens
    
    def _scan_token(self) -> None:
        """
        Scan and create the next token from the current position.
        
        This method handles all token recognition logic, including
        single-character tokens, multi-character tokens, and keywords.
        """
        char = self._advance()
        
        # Skip whitespace (except newlines)
        if char in ' \t\r':
            return
        
        # Handle newlines (statement separators)
        if char == '\n':
            self._add_token(TokenType.NEWLINE, char)
            self.line += 1
            self.column = 1
            return
        
        # Single-character tokens
        if char == '=':
            self._add_token(TokenType.ASSIGN, char)
        elif char == '+':
            self._add_token(TokenType.PLUS, char)
        elif char == '-':
            self._add_token(TokenType.MINUS, char)
        elif char == '*':
            self._add_token(TokenType.MULTIPLY, char)
        elif char == '/':
            self._add_token(TokenType.DIVIDE, char)
        
        # Numbers
        elif self._is_digit(char):
            self._scan_number()
        
        # Identifiers and keywords
        elif self._is_alpha(char):
            self._scan_identifier()
        
        # Invalid character
        else:
            raise LexicalError(f"Unexpected character: '{char}'", self.line, self.column - 1, char)
    
    def _scan_number(self) -> None:
        """
        Scan an integer literal.
        
        AEGIS only supports integer literals (no floating point).
        Numbers are sequences of digits.
        """
        start_pos = self.position - 1
        
        # Continue scanning digits
        while not self._is_at_end() and self._is_digit(self._peek()):
            self._advance()
        
        # Extract the number text
        number_text = self.source[start_pos:self.position]
        self._add_token(TokenType.INTEGER, number_text)
    
    def _scan_identifier(self) -> None:
        """
        Scan an identifier or keyword.
        
        Identifiers start with a letter or underscore and can contain
        letters, digits, and underscores. Keywords are recognized
        by comparing the identifier text.
        """
        start_pos = self.position - 1
        
        # Continue scanning alphanumeric characters and underscores
        while not self._is_at_end() and self._is_alphanumeric(self._peek()):
            self._advance()
        
        # Extract the identifier text
        identifier_text = self.source[start_pos:self.position]
        
        # Check if it's a keyword
        token_type = self._get_keyword_type(identifier_text)
        if token_type is None:
            token_type = TokenType.IDENTIFIER
        
        self._add_token(token_type, identifier_text)
    
    def _get_keyword_type(self, text: str) -> Optional[TokenType]:
        """
        Check if the given text is a keyword and return its token type.
        
        Args:
            text: The identifier text to check
            
        Returns:
            TokenType if it's a keyword, None if it's a regular identifier
        """
        keywords = {
            'print': TokenType.PRINT
        }
        return keywords.get(text)
    
    def _is_digit(self, char: str) -> bool:
        """Check if a character is a digit."""
        return char.isdigit()
    
    def _is_alpha(self, char: str) -> bool:
        """Check if a character is alphabetic or underscore."""
        return char.isalpha() or char == '_'
    
    def _is_alphanumeric(self, char: str) -> bool:
        """Check if a character is alphanumeric or underscore."""
        return char.isalnum() or char == '_'
    
    def _is_at_end(self) -> bool:
        """Check if we've reached the end of the source code."""
        return self.position >= len(self.source)
    
    def _advance(self) -> str:
        """
        Consume and return the current character, advancing position.
        
        Returns:
            The current character
        """
        if self._is_at_end():
            return '\0'
        
        char = self.source[self.position]
        self.position += 1
        self.column += 1
        return char
    
    def _peek(self) -> str:
        """
        Look at the current character without consuming it.
        
        Returns:
            The current character, or null character if at end
        """
        if self._is_at_end():
            return '\0'
        return self.source[self.position]
    
    def _add_token(self, token_type: TokenType, value: str) -> None:
        """
        Add a token to the tokens list.
        
        Args:
            token_type: The type of token to add
            value: The text value of the token
        """
        # Calculate the starting column for this token
        start_column = self.column - len(value)
        token = Token(token_type, value, self.line, start_column)
        self.tokens.append(token)