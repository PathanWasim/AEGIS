"""
Foundation tests for AEGIS system structure.

These tests verify that the basic project structure and imports
are working correctly before implementing the core functionality.
"""

import pytest
from aegis.lexer import Token, TokenType, Lexer
from aegis.parser import Parser
from aegis.ast import ASTNode, AssignmentNode, IntegerNode
from aegis.interpreter import ExecutionContext, ExecutionMode


class TestProjectStructure:
    """Test basic project structure and imports."""
    
    def test_token_creation(self):
        """Test that Token objects can be created."""
        token = Token(TokenType.INTEGER, "42", 1, 1)
        assert token.type == TokenType.INTEGER
        assert token.value == "42"
        assert token.line == 1
        assert token.column == 1
    
    def test_token_string_representation(self):
        """Test token string representation."""
        token = Token(TokenType.IDENTIFIER, "x", 2, 5)
        expected = "Token(IDENTIFIER, 'x', 2:5)"
        assert str(token) == expected
    
    def test_execution_context_creation(self):
        """Test that ExecutionContext can be created."""
        context = ExecutionContext()
        assert context.execution_mode == ExecutionMode.INTERPRETED
        assert len(context.variables) == 0
        assert len(context.output_buffer) == 0
    
    def test_execution_context_variable_operations(self):
        """Test variable operations in execution context."""
        context = ExecutionContext()
        
        # Test variable setting and getting
        context.set_variable("x", 42)
        assert context.get_variable("x") == 42
        assert context.is_variable_defined("x") is True
        assert context.is_variable_defined("y") is False
        
        # Test undefined variable access
        with pytest.raises(KeyError):
            context.get_variable("undefined")
    
    def test_execution_context_output_operations(self):
        """Test output operations in execution context."""
        context = ExecutionContext()
        
        context.add_output("Hello")
        context.add_output("World")
        
        assert context.get_output() == "Hello\nWorld"
        
        context.clear_output()
        assert context.get_output() == ""
    
    def test_execution_context_reset(self):
        """Test execution context reset functionality."""
        context = ExecutionContext()
        context.set_variable("x", 42)
        context.add_output("test")
        context.code_hash = "abc123"
        
        context.reset()
        
        assert len(context.variables) == 0
        assert len(context.output_buffer) == 0
        assert context.execution_mode == ExecutionMode.INTERPRETED
        assert context.code_hash == ""
    
    def test_ast_node_creation(self):
        """Test that AST nodes can be created."""
        # Test integer node
        int_node = IntegerNode(42)
        assert int_node.value == 42
        assert len(int_node.get_children()) == 0
        
        # Test that AssignmentNode can be created (placeholder test)
        # Full testing will be done when parser is implemented
        # This just verifies the structure exists
        from aegis.ast.nodes import IdentifierNode
        identifier = IdentifierNode("x")
        assignment = AssignmentNode("x", identifier)
        assert assignment.identifier == "x"
        assert assignment.expression == identifier
    
    def test_lexer_implementation(self):
        """Test that lexer implementation works correctly."""
        lexer = Lexer()
        tokens = lexer.tokenize("x = 42")
        
        # Should return proper tokens now
        assert len(tokens) == 4  # identifier, assign, integer, EOF
        assert tokens[0].type == TokenType.IDENTIFIER
        assert tokens[1].type == TokenType.ASSIGN
        assert tokens[2].type == TokenType.INTEGER
        assert tokens[3].type == TokenType.EOF
    
    def test_parser_placeholder(self):
        """Test that parser placeholder works."""
        parser = Parser()
        tokens = [Token(TokenType.EOF, "", 1, 1)]
        ast = parser.parse(tokens)
        
        # Placeholder should return empty AST
        assert len(ast) == 0


class TestTokenTypes:
    """Test all token types are defined correctly."""
    
    def test_all_token_types_exist(self):
        """Test that all required token types are defined."""
        required_types = [
            'IDENTIFIER', 'INTEGER', 'ASSIGN', 'PLUS', 'MINUS',
            'MULTIPLY', 'DIVIDE', 'PRINT', 'EOF', 'NEWLINE'
        ]
        
        for token_type in required_types:
            assert hasattr(TokenType, token_type)
            assert isinstance(getattr(TokenType, token_type), TokenType)
    
    def test_token_type_uniqueness(self):
        """Test that all token types have unique values."""
        token_values = [token_type.value for token_type in TokenType]
        assert len(token_values) == len(set(token_values))