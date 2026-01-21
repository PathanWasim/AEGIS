"""
Tests for the AEGIS lexer implementation.

These tests verify that the lexer correctly tokenizes AEGIS source code
and handles various edge cases and error conditions.
"""

import pytest
from aegis.lexer import Lexer, LexerError, Token, TokenType


class TestLexerBasicTokenization:
    """Test basic tokenization functionality."""
    
    def test_empty_source(self):
        """Test tokenizing empty source code."""
        lexer = Lexer()
        tokens = lexer.tokenize("")
        
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.EOF
    
    def test_single_identifier(self):
        """Test tokenizing a single identifier."""
        lexer = Lexer()
        tokens = lexer.tokenize("x")
        
        assert len(tokens) == 2  # identifier + EOF
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[0].value == "x"
        assert tokens[0].line == 1
        assert tokens[0].column == 1
        assert tokens[1].type == TokenType.EOF
    
    def test_single_integer(self):
        """Test tokenizing a single integer."""
        lexer = Lexer()
        tokens = lexer.tokenize("42")
        
        assert len(tokens) == 2  # integer + EOF
        assert tokens[0].type == TokenType.INTEGER
        assert tokens[0].value == "42"
        assert tokens[0].line == 1
        assert tokens[0].column == 1
        assert tokens[1].type == TokenType.EOF
    
    def test_assignment_statement(self):
        """Test tokenizing a simple assignment statement."""
        lexer = Lexer()
        tokens = lexer.tokenize("x = 10")
        
        expected_tokens = [
            (TokenType.IDENTIFIER, "x"),
            (TokenType.ASSIGN, "="),
            (TokenType.INTEGER, "10"),
            (TokenType.EOF, "")
        ]
        
        assert len(tokens) == len(expected_tokens)
        for i, (expected_type, expected_value) in enumerate(expected_tokens):
            assert tokens[i].type == expected_type
            assert tokens[i].value == expected_value
    
    def test_arithmetic_expression(self):
        """Test tokenizing arithmetic expressions."""
        lexer = Lexer()
        tokens = lexer.tokenize("x + y - 5 * 2 / z")
        
        expected_types = [
            TokenType.IDENTIFIER,  # x
            TokenType.PLUS,        # +
            TokenType.IDENTIFIER,  # y
            TokenType.MINUS,       # -
            TokenType.INTEGER,     # 5
            TokenType.MULTIPLY,    # *
            TokenType.INTEGER,     # 2
            TokenType.DIVIDE,      # /
            TokenType.IDENTIFIER,  # z
            TokenType.EOF
        ]
        
        assert len(tokens) == len(expected_types)
        for i, expected_type in enumerate(expected_types):
            assert tokens[i].type == expected_type
    
    def test_print_statement(self):
        """Test tokenizing print statements."""
        lexer = Lexer()
        tokens = lexer.tokenize("print x")
        
        expected_tokens = [
            (TokenType.PRINT, "print"),
            (TokenType.IDENTIFIER, "x"),
            (TokenType.EOF, "")
        ]
        
        assert len(tokens) == len(expected_tokens)
        for i, (expected_type, expected_value) in enumerate(expected_tokens):
            assert tokens[i].type == expected_type
            assert tokens[i].value == expected_value


class TestLexerWhitespaceHandling:
    """Test whitespace and newline handling."""
    
    def test_whitespace_skipping(self):
        """Test that whitespace is properly skipped."""
        lexer = Lexer()
        tokens = lexer.tokenize("  x   =    42  ")
        
        expected_tokens = [
            (TokenType.IDENTIFIER, "x"),
            (TokenType.ASSIGN, "="),
            (TokenType.INTEGER, "42"),
            (TokenType.EOF, "")
        ]
        
        assert len(tokens) == len(expected_tokens)
        for i, (expected_type, expected_value) in enumerate(expected_tokens):
            assert tokens[i].type == expected_type
            assert tokens[i].value == expected_value
    
    def test_newline_handling(self):
        """Test that newlines are tokenized as statement separators."""
        lexer = Lexer()
        tokens = lexer.tokenize("x = 10\ny = 20")
        
        expected_types = [
            TokenType.IDENTIFIER,  # x
            TokenType.ASSIGN,      # =
            TokenType.INTEGER,     # 10
            TokenType.NEWLINE,     # \n
            TokenType.IDENTIFIER,  # y
            TokenType.ASSIGN,      # =
            TokenType.INTEGER,     # 20
            TokenType.EOF
        ]
        
        assert len(tokens) == len(expected_types)
        for i, expected_type in enumerate(expected_types):
            assert tokens[i].type == expected_type
    
    def test_multiple_newlines(self):
        """Test handling of multiple consecutive newlines."""
        lexer = Lexer()
        tokens = lexer.tokenize("x = 10\n\n\ny = 20")
        
        # Should have 3 newline tokens
        newline_count = sum(1 for token in tokens if token.type == TokenType.NEWLINE)
        assert newline_count == 3


class TestLexerPositionTracking:
    """Test line and column position tracking."""
    
    def test_single_line_positions(self):
        """Test column positions on a single line."""
        lexer = Lexer()
        tokens = lexer.tokenize("x = 42")
        
        # x should be at column 1
        assert tokens[0].column == 1
        # = should be at column 3
        assert tokens[1].column == 3
        # 42 should be at column 5
        assert tokens[2].column == 5
    
    def test_multiline_positions(self):
        """Test line and column positions across multiple lines."""
        lexer = Lexer()
        tokens = lexer.tokenize("x = 10\ny = 20")
        
        # First line tokens
        assert tokens[0].line == 1  # x
        assert tokens[1].line == 1  # =
        assert tokens[2].line == 1  # 10
        assert tokens[3].line == 1  # \n
        
        # Second line tokens
        assert tokens[4].line == 2  # y
        assert tokens[5].line == 2  # =
        assert tokens[6].line == 2  # 20
        
        # Column positions on second line
        assert tokens[4].column == 1  # y
        assert tokens[5].column == 3  # =
        assert tokens[6].column == 5  # 20


class TestLexerIdentifiers:
    """Test identifier recognition."""
    
    def test_simple_identifiers(self):
        """Test simple identifier recognition."""
        lexer = Lexer()
        
        test_cases = ["x", "variable", "counter", "result"]
        
        for identifier in test_cases:
            tokens = lexer.tokenize(identifier)
            assert tokens[0].type == TokenType.IDENTIFIER
            assert tokens[0].value == identifier
    
    def test_identifiers_with_underscores(self):
        """Test identifiers with underscores."""
        lexer = Lexer()
        
        test_cases = ["_x", "var_name", "my_variable", "_private_var"]
        
        for identifier in test_cases:
            tokens = lexer.tokenize(identifier)
            assert tokens[0].type == TokenType.IDENTIFIER
            assert tokens[0].value == identifier
    
    def test_identifiers_with_numbers(self):
        """Test identifiers with numbers."""
        lexer = Lexer()
        
        test_cases = ["x1", "var2", "counter123", "result_1"]
        
        for identifier in test_cases:
            tokens = lexer.tokenize(identifier)
            assert tokens[0].type == TokenType.IDENTIFIER
            assert tokens[0].value == identifier


class TestLexerNumbers:
    """Test number recognition."""
    
    def test_single_digit_numbers(self):
        """Test single digit numbers."""
        lexer = Lexer()
        
        for digit in "0123456789":
            tokens = lexer.tokenize(digit)
            assert tokens[0].type == TokenType.INTEGER
            assert tokens[0].value == digit
    
    def test_multi_digit_numbers(self):
        """Test multi-digit numbers."""
        lexer = Lexer()
        
        test_cases = ["10", "42", "123", "999", "1000"]
        
        for number in test_cases:
            tokens = lexer.tokenize(number)
            assert tokens[0].type == TokenType.INTEGER
            assert tokens[0].value == number


class TestLexerKeywords:
    """Test keyword recognition."""
    
    def test_print_keyword(self):
        """Test that 'print' is recognized as a keyword."""
        lexer = Lexer()
        tokens = lexer.tokenize("print")
        
        assert tokens[0].type == TokenType.PRINT
        assert tokens[0].value == "print"
    
    def test_print_vs_identifier(self):
        """Test that print-like identifiers are not keywords."""
        lexer = Lexer()
        
        # These should be identifiers, not keywords
        test_cases = ["printer", "print_var", "printing"]
        
        for identifier in test_cases:
            tokens = lexer.tokenize(identifier)
            assert tokens[0].type == TokenType.IDENTIFIER
            assert tokens[0].value == identifier


class TestLexerErrorHandling:
    """Test error handling and invalid input."""
    
    def test_invalid_character(self):
        """Test that invalid characters raise LexerError."""
        lexer = Lexer()
        
        invalid_chars = ["@", "#", "$", "%", "^", "&", "(", ")", "[", "]", "{", "}", "?"]
        
        for char in invalid_chars:
            with pytest.raises(LexerError) as exc_info:
                lexer.tokenize(char)
            
            assert "Unexpected character" in str(exc_info.value)
            assert char in str(exc_info.value)
    
    def test_error_position_reporting(self):
        """Test that errors include correct position information."""
        lexer = Lexer()
        
        with pytest.raises(LexerError) as exc_info:
            lexer.tokenize("x = @")
        
        error = exc_info.value
        assert error.line == 1
        assert error.column == 5  # @ is at position 5 (1-based indexing)


class TestLexerCompletePrograms:
    """Test tokenizing complete AEGIS programs."""
    
    def test_simple_program(self):
        """Test tokenizing a simple complete program."""
        lexer = Lexer()
        source = """x = 10
y = x + 5
print y"""
        
        tokens = lexer.tokenize(source)
        
        expected_types = [
            TokenType.IDENTIFIER,  # x
            TokenType.ASSIGN,      # =
            TokenType.INTEGER,     # 10
            TokenType.NEWLINE,     # \n
            TokenType.IDENTIFIER,  # y
            TokenType.ASSIGN,      # =
            TokenType.IDENTIFIER,  # x
            TokenType.PLUS,        # +
            TokenType.INTEGER,     # 5
            TokenType.NEWLINE,     # \n
            TokenType.PRINT,       # print
            TokenType.IDENTIFIER,  # y
            TokenType.EOF
        ]
        
        assert len(tokens) == len(expected_types)
        for i, expected_type in enumerate(expected_types):
            assert tokens[i].type == expected_type
    
    def test_arithmetic_program(self):
        """Test tokenizing a program with complex arithmetic."""
        lexer = Lexer()
        source = """result = 10 + 5 * 2 - 8 / 4
print result"""
        
        tokens = lexer.tokenize(source)
        
        # Verify we get all the expected operators
        operator_types = [token.type for token in tokens if token.type in [
            TokenType.PLUS, TokenType.MINUS, TokenType.MULTIPLY, TokenType.DIVIDE
        ]]
        
        expected_operators = [TokenType.PLUS, TokenType.MULTIPLY, TokenType.MINUS, TokenType.DIVIDE]
        assert operator_types == expected_operators