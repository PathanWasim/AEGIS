"""
Recursive descent parser implementation for AEGIS.

This module implements a recursive descent parser that converts tokens
from the lexer into an Abstract Syntax Tree (AST). The parser handles
the AEGIS grammar with proper precedence and associativity.

Grammar:
    program     → statement* EOF
    statement   → assignment | print_stmt
    assignment  → IDENTIFIER "=" expression
    print_stmt  → "print" IDENTIFIER
    expression  → term ( ( "+" | "-" ) term )*
    term        → factor ( ( "*" | "/" ) factor )*
    factor      → INTEGER | IDENTIFIER | "(" expression ")"
"""

from typing import List, Optional
from ..lexer.tokens import Token, TokenType
from ..ast.nodes import (
    ASTNode, AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode, ExpressionNode
)


class ParseError(Exception):
    """
    Exception raised for parsing errors.
    
    Includes position information for precise error reporting.
    """
    
    def __init__(self, message: str, token: Token):
        self.message = message
        self.token = token
        super().__init__(f"Parse error at line {token.line}, column {token.column}: {message}")


class Parser:
    """
    Recursive descent parser for the AEGIS language.
    
    This parser implements a top-down parsing approach, where each
    grammar rule is implemented as a method. The parser maintains
    a current position in the token stream and advances through
    tokens as it builds the AST.
    
    The parser handles:
    - Variable assignments (x = expression)
    - Arithmetic expressions with proper precedence (+, -, *, /)
    - Print statements (print identifier)
    - Syntax error detection with location information
    """
    
    def __init__(self):
        """Initialize the parser."""
        self.tokens = []
        self.current = 0
    
    def parse(self, tokens: List[Token]) -> List[ASTNode]:
        """
        Parse tokens into an Abstract Syntax Tree.
        
        Args:
            tokens: List of tokens from the lexer
            
        Returns:
            List of AST nodes representing the program statements
            
        Raises:
            ParseError: If syntax errors are encountered
        """
        self.tokens = tokens
        self.current = 0
        
        statements = []
        
        while not self._is_at_end():
            # Skip newlines between statements
            if self._check(TokenType.NEWLINE):
                self._advance()
                continue
            
            # Parse statement
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
        
        return statements
    
    def _parse_statement(self) -> Optional[ASTNode]:
        """
        Parse a single statement.
        
        Returns:
            AST node for the statement, or None if no statement found
            
        Raises:
            ParseError: If syntax errors are encountered
        """
        # Check for print statement
        if self._check(TokenType.PRINT):
            return self._parse_print_statement()
        
        # Check for assignment (identifier = expression)
        if self._check(TokenType.IDENTIFIER):
            return self._parse_assignment()
        
        # If we reach EOF, return None
        if self._check(TokenType.EOF):
            return None
        
        # Unexpected token
        current_token = self._peek()
        raise ParseError(f"Unexpected token: {current_token.value}", current_token)
    
    def _parse_assignment(self) -> AssignmentNode:
        """
        Parse an assignment statement: identifier = expression
        
        Returns:
            AssignmentNode representing the assignment
            
        Raises:
            ParseError: If syntax errors are encountered
        """
        # Get the identifier
        identifier_token = self._consume(TokenType.IDENTIFIER, "Expected identifier")
        identifier = identifier_token.value
        
        # Expect assignment operator
        self._consume(TokenType.ASSIGN, "Expected '=' after identifier")
        
        # Parse the expression
        expression = self._parse_expression()
        
        return AssignmentNode(identifier, expression)
    
    def _parse_print_statement(self) -> PrintNode:
        """
        Parse a print statement: print identifier
        
        Returns:
            PrintNode representing the print statement
            
        Raises:
            ParseError: If syntax errors are encountered
        """
        # Consume 'print' keyword
        self._consume(TokenType.PRINT, "Expected 'print'")
        
        # Get the identifier to print
        identifier_token = self._consume(TokenType.IDENTIFIER, "Expected identifier after 'print'")
        identifier = identifier_token.value
        
        return PrintNode(identifier)
    
    def _parse_expression(self) -> ExpressionNode:
        """
        Parse an expression with addition and subtraction.
        
        Grammar: expression → term ( ( "+" | "-" ) term )*
        
        Returns:
            ExpressionNode representing the expression
        """
        expr = self._parse_term()
        
        while self._match(TokenType.PLUS, TokenType.MINUS):
            operator = self._previous().value
            right = self._parse_term()
            expr = BinaryOpNode(expr, operator, right)
        
        return expr
    
    def _parse_term(self) -> ExpressionNode:
        """
        Parse a term with multiplication and division.
        
        Grammar: term → factor ( ( "*" | "/" ) factor )*
        
        Returns:
            ExpressionNode representing the term
        """
        expr = self._parse_factor()
        
        while self._match(TokenType.MULTIPLY, TokenType.DIVIDE):
            operator = self._previous().value
            right = self._parse_factor()
            expr = BinaryOpNode(expr, operator, right)
        
        return expr
    
    def _parse_factor(self) -> ExpressionNode:
        """
        Parse a factor (primary expression).
        
        Grammar: factor → INTEGER | IDENTIFIER | "(" expression ")"
        
        Returns:
            ExpressionNode representing the factor
            
        Raises:
            ParseError: If syntax errors are encountered
        """
        # Integer literal
        if self._match(TokenType.INTEGER):
            value = int(self._previous().value)
            return IntegerNode(value)
        
        # Identifier (variable reference)
        if self._match(TokenType.IDENTIFIER):
            name = self._previous().value
            return IdentifierNode(name)
        
        # Parenthesized expression (not implemented in basic AEGIS)
        # Could be added later for more complex expressions
        
        # If we get here, we have an unexpected token
        current_token = self._peek()
        raise ParseError(f"Expected expression, got: {current_token.value}", current_token)
    
    def _match(self, *token_types: TokenType) -> bool:
        """
        Check if current token matches any of the given types and advance if so.
        
        Args:
            token_types: Token types to match against
            
        Returns:
            True if current token matches and was consumed
        """
        for token_type in token_types:
            if self._check(token_type):
                self._advance()
                return True
        return False
    
    def _check(self, token_type: TokenType) -> bool:
        """
        Check if current token is of the given type without consuming it.
        
        Args:
            token_type: Token type to check
            
        Returns:
            True if current token matches the type
        """
        if self._is_at_end():
            return False
        return self._peek().type == token_type
    
    def _advance(self) -> Token:
        """
        Consume and return the current token.
        
        Returns:
            The consumed token
        """
        if not self._is_at_end():
            self.current += 1
        return self._previous()
    
    def _is_at_end(self) -> bool:
        """
        Check if we've reached the end of the token stream.
        
        Returns:
            True if at end of tokens
        """
        return self._peek().type == TokenType.EOF
    
    def _peek(self) -> Token:
        """
        Return the current token without consuming it.
        
        Returns:
            The current token
        """
        return self.tokens[self.current]
    
    def _previous(self) -> Token:
        """
        Return the previous token.
        
        Returns:
            The previous token
        """
        return self.tokens[self.current - 1]
    
    def _consume(self, token_type: TokenType, message: str) -> Token:
        """
        Consume a token of the expected type or raise an error.
        
        Args:
            token_type: Expected token type
            message: Error message if token doesn't match
            
        Returns:
            The consumed token
            
        Raises:
            ParseError: If token doesn't match expected type
        """
        if self._check(token_type):
            return self._advance()
        
        current_token = self._peek()
        raise ParseError(f"{message}, got: {current_token.value}", current_token)