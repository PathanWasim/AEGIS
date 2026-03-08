"""
Recursive descent parser implementation for AEGIS.

This module converts a token stream produced by the Lexer into an Abstract
Syntax Tree.  The grammar has been extended to support control flow:

Grammar (EBNF):
    program     → statement* EOF
    statement   → if_stmt | while_stmt | assignment | print_stmt
    if_stmt     → "if" comparison NEWLINE
                      statement*
                  ("else" NEWLINE statement*)?
                  "end"
    while_stmt  → "while" comparison NEWLINE
                      statement*
                  "end"
    assignment  → IDENTIFIER "=" expression
    print_stmt  → "print" expression
    expression  → comparison
    comparison  → term (( ">"  | "<"  | ">=" | "<=" | "==" | "!=" ) term)*
    term        → factor (( "+" | "-" ) factor)*
    factor      → unary  (( "*" | "/" | "%" ) unary)*
    unary       → "-" unary | primary
    primary     → INTEGER | IDENTIFIER | "(" expression ")"
"""

from typing import List, Optional
from ..lexer.tokens import Token, TokenType
from ..ast.nodes import (
    ASTNode, AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode, IfNode, WhileNode, ExpressionNode
)
from ..errors import SyntaxError as AegisSyntaxError


class Parser:
    """
    Recursive descent parser for the AEGIS language.

    Parses the extended AEGIS grammar that now supports:
    - Variable assignments with full expressions on the RHS
    - print <expression>  (can print any expression, not just identifiers)
    - if/else/end  control flow
    - while/end    loops
    - Comparison operators: >, <, >=, <=, ==, !=
    - Arithmetic:  +, -, *, /, %
    - Unary minus: -x
    - Parenthesised expressions: (x + 1)
    """

    def __init__(self):
        """Initialise the parser."""
        self.tokens: List[Token] = []
        self.current: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(self, tokens: List[Token]) -> List[ASTNode]:
        """
        Parse a token list into a list of top-level statement nodes.

        Args:
            tokens: Token list from the Lexer (must end with EOF).

        Returns:
            List of AST statement nodes.

        Raises:
            AegisSyntaxError: On any grammar violation.
        """
        self.tokens = tokens
        self.current = 0
        return self._parse_block_until(TokenType.EOF)

    # ------------------------------------------------------------------
    # Block-level helpers
    # ------------------------------------------------------------------

    def _parse_block_until(self, *stop_types: TokenType) -> List[ASTNode]:
        """
        Parse statements until a stop token is found.

        The stop token is *not* consumed by this method.
        """
        statements: List[ASTNode] = []
        while not self._is_at_end() and not self._check(*stop_types):
            self._skip_newlines()
            if self._is_at_end() or self._check(*stop_types):
                break
            stmt = self._parse_statement()
            if stmt is not None:
                statements.append(stmt)
        return statements

    def _skip_newlines(self) -> None:
        while self._check(TokenType.NEWLINE):
            self._advance()

    # ------------------------------------------------------------------
    # Statement parsing
    # ------------------------------------------------------------------

    def _parse_statement(self) -> Optional[ASTNode]:
        """Parse a single statement."""
        if self._check(TokenType.IF):
            return self._parse_if_statement()
        if self._check(TokenType.WHILE):
            return self._parse_while_statement()
        if self._check(TokenType.PRINT):
            return self._parse_print_statement()
        if self._check(TokenType.IDENTIFIER):
            return self._parse_assignment()
        if self._check(TokenType.EOF, TokenType.NEWLINE):
            self._advance()
            return None

        tok = self._peek()
        raise AegisSyntaxError(
            f"Unexpected token '{tok.value}' — expected a statement",
            tok.line, tok.column, tok.value, expected="statement"
        )

    # ---------------- if / else / end ---------------------------------

    def _parse_if_statement(self) -> IfNode:
        """
        Parse:
            if <condition>
                <body>
            [else
                <else_body>]
            end
        """
        self._consume(TokenType.IF, "Expected 'if'")
        condition = self._parse_expression()
        self._expect_newline("Expected newline after 'if' condition")

        then_body = self._parse_block_until(TokenType.ELSE, TokenType.END)

        else_body: List[ASTNode] = []
        if self._match(TokenType.ELSE):
            self._expect_newline("Expected newline after 'else'")
            else_body = self._parse_block_until(TokenType.END)

        self._consume(TokenType.END, "Expected 'end' to close 'if' block")
        return IfNode(condition, then_body, else_body)

    # ---------------- while / end -------------------------------------

    def _parse_while_statement(self) -> WhileNode:
        """
        Parse:
            while <condition>
                <body>
            end
        """
        self._consume(TokenType.WHILE, "Expected 'while'")
        condition = self._parse_expression()
        self._expect_newline("Expected newline after 'while' condition")

        body = self._parse_block_until(TokenType.END)
        self._consume(TokenType.END, "Expected 'end' to close 'while' block")
        return WhileNode(condition, body)

    # ---------------- assignment --------------------------------------

    def _parse_assignment(self) -> AssignmentNode:
        """Parse:  IDENTIFIER = expression"""
        id_token = self._consume(TokenType.IDENTIFIER, "Expected identifier")
        self._consume(TokenType.ASSIGN, f"Expected '=' after '{id_token.value}'")
        expression = self._parse_expression()
        return AssignmentNode(id_token.value, expression)

    # ---------------- print -------------------------------------------

    def _parse_print_statement(self) -> PrintNode:
        """Parse:  print <expression>"""
        self._consume(TokenType.PRINT, "Expected 'print'")
        expression = self._parse_expression()
        return PrintNode(expression)

    # ------------------------------------------------------------------
    # Expression parsing  (precedence climbing)
    # ------------------------------------------------------------------

    def _parse_expression(self) -> ExpressionNode:
        """expression → comparison"""
        return self._parse_comparison()

    def _parse_comparison(self) -> ExpressionNode:
        """
        comparison → additive (( ">" | "<" | ">=" | "<=" | "==" | "!=" ) additive)*
        """
        expr = self._parse_additive()
        cmp_ops = (
            TokenType.GT, TokenType.LT,
            TokenType.GTE, TokenType.LTE,
            TokenType.EQ, TokenType.NEQ,
        )
        while self._match(*cmp_ops):
            op = self._previous().value
            right = self._parse_additive()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def _parse_additive(self) -> ExpressionNode:
        """additive → multiplicative (( "+" | "-" ) multiplicative)*"""
        expr = self._parse_multiplicative()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous().value
            right = self._parse_multiplicative()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def _parse_multiplicative(self) -> ExpressionNode:
        """multiplicative → unary (( "*" | "/" | "%" ) unary)*"""
        expr = self._parse_unary()
        while self._match(TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULO):
            op = self._previous().value
            right = self._parse_unary()
            expr = BinaryOpNode(expr, op, right)
        return expr

    def _parse_unary(self) -> ExpressionNode:
        """unary → "-" unary | primary"""
        if self._match(TokenType.MINUS):
            operand = self._parse_unary()
            # Represent -x as 0 - x
            return BinaryOpNode(IntegerNode(0), '-', operand)
        return self._parse_primary()

    def _parse_primary(self) -> ExpressionNode:
        """primary → INTEGER | IDENTIFIER | "(" expression ")" """
        if self._match(TokenType.INTEGER):
            return IntegerNode(int(self._previous().value))

        if self._match(TokenType.IDENTIFIER):
            return IdentifierNode(self._previous().value)

        if self._match(TokenType.LPAREN):
            expr = self._parse_expression()
            self._consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr

        tok = self._peek()
        raise AegisSyntaxError(
            f"Expected an expression but got '{tok.value}'",
            tok.line, tok.column, tok.value, "expression"
        )

    # ------------------------------------------------------------------
    # Token-stream utilities
    # ------------------------------------------------------------------

    def _expect_newline(self, message: str = "Expected newline") -> None:
        """Consume one or more newlines, raising SyntaxError if none found."""
        if not self._check(TokenType.NEWLINE):
            # Allow EOF to close lines too
            if self._check(TokenType.EOF):
                return
            tok = self._peek()
            raise AegisSyntaxError(message, tok.line, tok.column, tok.value, "newline")
        while self._check(TokenType.NEWLINE):
            self._advance()

    def _match(self, *token_types: TokenType) -> bool:
        """Consume the current token if its type is in token_types."""
        for tt in token_types:
            if self._check(tt):
                self._advance()
                return True
        return False

    def _check(self, *token_types: TokenType) -> bool:
        """True if current token type is any of token_types (no consumption)."""
        return self._peek().type in token_types

    def _advance(self) -> Token:
        """Consume and return the current token."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _consume(self, token_type: TokenType, message: str) -> Token:
        """Consume a token of the expected type or raise SyntaxError."""
        if self._check(token_type):
            return self._advance()
        tok = self._peek()
        raise AegisSyntaxError(
            f"{message}, got '{tok.value}'",
            tok.line, tok.column, tok.value,
            expected=token_type.name.lower()
        )