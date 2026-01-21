"""
Tests for the AEGIS parser implementation.

These tests verify that the parser correctly builds AST from tokens
and handles various syntax constructs and error conditions.
"""

import pytest
from aegis.lexer import Lexer, Token, TokenType
from aegis.parser import Parser, ParseError
from aegis.ast import (
    AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode, ASTPrettyPrinter
)


class TestParserBasicStatements:
    """Test parsing of basic statements."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.printer = ASTPrettyPrinter()
    
    def test_simple_assignment(self):
        """Test parsing simple assignment statements."""
        tokens = self.lexer.tokenize("x = 42")
        ast = self.parser.parse(tokens)
        
        assert len(ast) == 1
        assert isinstance(ast[0], AssignmentNode)
        assert ast[0].identifier == "x"
        assert isinstance(ast[0].expression, IntegerNode)
        assert ast[0].expression.value == 42
    
    def test_assignment_with_identifier(self):
        """Test assignment with identifier on right side."""
        tokens = self.lexer.tokenize("y = x")
        ast = self.parser.parse(tokens)
        
        assert len(ast) == 1
        assert isinstance(ast[0], AssignmentNode)
        assert ast[0].identifier == "y"
        assert isinstance(ast[0].expression, IdentifierNode)
        assert ast[0].expression.name == "x"
    
    def test_print_statement(self):
        """Test parsing print statements."""
        tokens = self.lexer.tokenize("print x")
        ast = self.parser.parse(tokens)
        
        assert len(ast) == 1
        assert isinstance(ast[0], PrintNode)
        assert ast[0].identifier == "x"
    
    def test_empty_program(self):
        """Test parsing empty program."""
        tokens = self.lexer.tokenize("")
        ast = self.parser.parse(tokens)
        
        assert len(ast) == 0


class TestParserArithmeticExpressions:
    """Test parsing of arithmetic expressions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.printer = ASTPrettyPrinter()
    
    def test_simple_addition(self):
        """Test parsing simple addition."""
        tokens = self.lexer.tokenize("result = 10 + 5")
        ast = self.parser.parse(tokens)
        
        assert len(ast) == 1
        assignment = ast[0]
        assert isinstance(assignment, AssignmentNode)
        assert assignment.identifier == "result"
        
        expr = assignment.expression
        assert isinstance(expr, BinaryOpNode)
        assert expr.operator == "+"
        assert isinstance(expr.left, IntegerNode)
        assert expr.left.value == 10
        assert isinstance(expr.right, IntegerNode)
        assert expr.right.value == 5
    
    def test_simple_subtraction(self):
        """Test parsing simple subtraction."""
        tokens = self.lexer.tokenize("result = 10 - 3")
        ast = self.parser.parse(tokens)
        
        assignment = ast[0]
        expr = assignment.expression
        assert isinstance(expr, BinaryOpNode)
        assert expr.operator == "-"
        assert expr.left.value == 10
        assert expr.right.value == 3
    
    def test_simple_multiplication(self):
        """Test parsing simple multiplication."""
        tokens = self.lexer.tokenize("result = 6 * 7")
        ast = self.parser.parse(tokens)
        
        assignment = ast[0]
        expr = assignment.expression
        assert isinstance(expr, BinaryOpNode)
        assert expr.operator == "*"
        assert expr.left.value == 6
        assert expr.right.value == 7
    
    def test_simple_division(self):
        """Test parsing simple division."""
        tokens = self.lexer.tokenize("result = 20 / 4")
        ast = self.parser.parse(tokens)
        
        assignment = ast[0]
        expr = assignment.expression
        assert isinstance(expr, BinaryOpNode)
        assert expr.operator == "/"
        assert expr.left.value == 20
        assert expr.right.value == 4
    
    def test_operator_precedence_multiply_first(self):
        """Test that multiplication has higher precedence than addition."""
        tokens = self.lexer.tokenize("result = 2 + 3 * 4")
        ast = self.parser.parse(tokens)
        
        assignment = ast[0]
        expr = assignment.expression
        
        # Should parse as: 2 + (3 * 4)
        assert isinstance(expr, BinaryOpNode)
        assert expr.operator == "+"
        assert isinstance(expr.left, IntegerNode)
        assert expr.left.value == 2
        
        # Right side should be multiplication
        assert isinstance(expr.right, BinaryOpNode)
        assert expr.right.operator == "*"
        assert expr.right.left.value == 3
        assert expr.right.right.value == 4
    
    def test_operator_precedence_divide_first(self):
        """Test that division has higher precedence than subtraction."""
        tokens = self.lexer.tokenize("result = 10 - 8 / 2")
        ast = self.parser.parse(tokens)
        
        assignment = ast[0]
        expr = assignment.expression
        
        # Should parse as: 10 - (8 / 2)
        assert isinstance(expr, BinaryOpNode)
        assert expr.operator == "-"
        assert expr.left.value == 10
        assert isinstance(expr.right, BinaryOpNode)
        assert expr.right.operator == "/"
        assert expr.right.left.value == 8
        assert expr.right.right.value == 2
    
    def test_left_associativity_addition(self):
        """Test that addition is left-associative."""
        tokens = self.lexer.tokenize("result = 1 + 2 + 3")
        ast = self.parser.parse(tokens)
        
        assignment = ast[0]
        expr = assignment.expression
        
        # Should parse as: (1 + 2) + 3
        assert isinstance(expr, BinaryOpNode)
        assert expr.operator == "+"
        assert expr.right.value == 3
        
        # Left side should be another addition
        assert isinstance(expr.left, BinaryOpNode)
        assert expr.left.operator == "+"
        assert expr.left.left.value == 1
        assert expr.left.right.value == 2
    
    def test_left_associativity_multiplication(self):
        """Test that multiplication is left-associative."""
        tokens = self.lexer.tokenize("result = 2 * 3 * 4")
        ast = self.parser.parse(tokens)
        
        assignment = ast[0]
        expr = assignment.expression
        
        # Should parse as: (2 * 3) * 4
        assert isinstance(expr, BinaryOpNode)
        assert expr.operator == "*"
        assert expr.right.value == 4
        assert isinstance(expr.left, BinaryOpNode)
        assert expr.left.operator == "*"
        assert expr.left.left.value == 2
        assert expr.left.right.value == 3
    
    def test_complex_expression(self):
        """Test parsing complex expressions with mixed operators."""
        tokens = self.lexer.tokenize("result = 1 + 2 * 3 - 4 / 2")
        ast = self.parser.parse(tokens)
        
        assignment = ast[0]
        expr = assignment.expression
        
        # Should parse as: ((1 + (2 * 3)) - (4 / 2))
        # Verify the structure by pretty-printing
        pretty = self.printer.print_ast(expr)
        assert "1 + 2 * 3 - 4 / 2" == pretty
    
    def test_expression_with_variables(self):
        """Test expressions with variable references."""
        tokens = self.lexer.tokenize("result = x + y * z")
        ast = self.parser.parse(tokens)
        
        assignment = ast[0]
        expr = assignment.expression
        
        assert isinstance(expr, BinaryOpNode)
        assert expr.operator == "+"
        assert isinstance(expr.left, IdentifierNode)
        assert expr.left.name == "x"
        
        # Right side should be y * z
        assert isinstance(expr.right, BinaryOpNode)
        assert expr.right.operator == "*"
        assert expr.right.left.name == "y"
        assert expr.right.right.name == "z"


class TestParserMultipleStatements:
    """Test parsing programs with multiple statements."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.printer = ASTPrettyPrinter()
    
    def test_multiple_assignments(self):
        """Test parsing multiple assignment statements."""
        source = """x = 10
y = 20
z = x + y"""
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        assert len(ast) == 3
        
        # First assignment: x = 10
        assert isinstance(ast[0], AssignmentNode)
        assert ast[0].identifier == "x"
        assert ast[0].expression.value == 10
        
        # Second assignment: y = 20
        assert isinstance(ast[1], AssignmentNode)
        assert ast[1].identifier == "y"
        assert ast[1].expression.value == 20
        
        # Third assignment: z = x + y
        assert isinstance(ast[2], AssignmentNode)
        assert ast[2].identifier == "z"
        assert isinstance(ast[2].expression, BinaryOpNode)
    
    def test_assignment_and_print(self):
        """Test parsing assignment followed by print."""
        source = """result = 42
print result"""
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        assert len(ast) == 2
        assert isinstance(ast[0], AssignmentNode)
        assert isinstance(ast[1], PrintNode)
        assert ast[1].identifier == "result"
    
    def test_complete_program(self):
        """Test parsing a complete AEGIS program."""
        source = """x = 10
y = 20
sum = x + y
product = x * y
print sum
print product"""
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        assert len(ast) == 6
        
        # Verify statement types
        expected_types = [
            AssignmentNode, AssignmentNode, AssignmentNode,
            AssignmentNode, PrintNode, PrintNode
        ]
        
        for i, expected_type in enumerate(expected_types):
            assert isinstance(ast[i], expected_type)
    
    def test_program_with_empty_lines(self):
        """Test parsing program with empty lines (multiple newlines)."""
        source = """x = 10

y = 20


print x"""
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        
        # Should ignore empty lines and parse 3 statements
        assert len(ast) == 3
        assert isinstance(ast[0], AssignmentNode)
        assert isinstance(ast[1], AssignmentNode)
        assert isinstance(ast[2], PrintNode)


class TestParserErrorHandling:
    """Test parser error handling and syntax error detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
    
    def test_missing_assignment_operator(self):
        """Test error when assignment operator is missing."""
        tokens = self.lexer.tokenize("x 42")
        
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(tokens)
        
        assert "Expected '='" in str(exc_info.value)
    
    def test_missing_expression_after_assignment(self):
        """Test error when expression is missing after assignment."""
        # Create tokens manually to simulate incomplete assignment
        tokens = [
            Token(TokenType.IDENTIFIER, "x", 1, 1),
            Token(TokenType.ASSIGN, "=", 1, 3),
            Token(TokenType.EOF, "", 1, 4)
        ]
        
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(tokens)
        
        assert "Expected expression" in str(exc_info.value)
    
    def test_missing_identifier_after_print(self):
        """Test error when identifier is missing after print."""
        # Create tokens manually
        tokens = [
            Token(TokenType.PRINT, "print", 1, 1),
            Token(TokenType.EOF, "", 1, 6)
        ]
        
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(tokens)
        
        assert "Expected identifier after 'print'" in str(exc_info.value)
    
    def test_invalid_expression_start(self):
        """Test error when expression starts with invalid token."""
        # Create tokens for: x = =
        tokens = [
            Token(TokenType.IDENTIFIER, "x", 1, 1),
            Token(TokenType.ASSIGN, "=", 1, 3),
            Token(TokenType.ASSIGN, "=", 1, 5),
            Token(TokenType.EOF, "", 1, 6)
        ]
        
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(tokens)
        
        assert "Expected expression" in str(exc_info.value)
    
    def test_unexpected_token_at_statement_level(self):
        """Test error when unexpected token appears at statement level."""
        # Create tokens for: + x
        tokens = [
            Token(TokenType.PLUS, "+", 1, 1),
            Token(TokenType.IDENTIFIER, "x", 1, 3),
            Token(TokenType.EOF, "", 1, 4)
        ]
        
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(tokens)
        
        assert "Unexpected token" in str(exc_info.value)
    
    def test_error_position_reporting(self):
        """Test that parse errors include correct position information."""
        tokens = [
            Token(TokenType.IDENTIFIER, "x", 2, 5),
            Token(TokenType.PLUS, "+", 2, 7),  # Invalid - should be =
            Token(TokenType.EOF, "", 2, 8)
        ]
        
        with pytest.raises(ParseError) as exc_info:
            self.parser.parse(tokens)
        
        error = exc_info.value
        assert error.token.line == 2
        assert error.token.column == 7


class TestParserRoundTrip:
    """Test that parsing and pretty-printing produces equivalent programs."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.printer = ASTPrettyPrinter()
    
    def test_simple_assignment_roundtrip(self):
        """Test round-trip for simple assignment."""
        source = "x = 42"
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        reconstructed = self.printer.print_program(ast)
        
        assert reconstructed == source
    
    def test_arithmetic_expression_roundtrip(self):
        """Test round-trip for arithmetic expressions."""
        source = "result = 1 + 2 * 3"
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        reconstructed = self.printer.print_program(ast)
        
        assert reconstructed == source
    
    def test_print_statement_roundtrip(self):
        """Test round-trip for print statements."""
        source = "print x"
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        reconstructed = self.printer.print_program(ast)
        
        assert reconstructed == source
    
    def test_complete_program_roundtrip(self):
        """Test round-trip for complete program."""
        source = """x = 10
y = x + 5
print y"""
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        reconstructed = self.printer.print_program(ast)
        
        assert reconstructed == source
    
    def test_complex_expression_roundtrip(self):
        """Test round-trip for complex expressions."""
        source = "result = a + b * c - d / e"
        
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        reconstructed = self.printer.print_program(ast)
        
        assert reconstructed == source