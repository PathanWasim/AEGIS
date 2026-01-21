"""
Tests for the AEGIS AST implementation.

These tests verify that AST nodes are created correctly and that
the pretty printer can convert AST back to equivalent source code.
"""

import pytest
from aegis.ast import (
    ASTNode, AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode, ASTPrettyPrinter
)


class TestASTNodes:
    """Test AST node creation and basic functionality."""
    
    def test_integer_node_creation(self):
        """Test creating integer nodes."""
        node = IntegerNode(42)
        assert node.value == 42
        assert len(node.get_children()) == 0
    
    def test_identifier_node_creation(self):
        """Test creating identifier nodes."""
        node = IdentifierNode("variable_name")
        assert node.name == "variable_name"
        assert len(node.get_children()) == 0
    
    def test_binary_op_node_creation(self):
        """Test creating binary operation nodes."""
        left = IntegerNode(10)
        right = IntegerNode(5)
        node = BinaryOpNode(left, "+", right)
        
        assert node.left == left
        assert node.operator == "+"
        assert node.right == right
        assert len(node.get_children()) == 2
        assert node.get_children() == [left, right]
    
    def test_assignment_node_creation(self):
        """Test creating assignment nodes."""
        expression = IntegerNode(42)
        node = AssignmentNode("x", expression)
        
        assert node.identifier == "x"
        assert node.expression == expression
        assert len(node.get_children()) == 1
        assert node.get_children() == [expression]
    
    def test_print_node_creation(self):
        """Test creating print nodes."""
        node = PrintNode("result")
        assert node.identifier == "result"
        assert len(node.get_children()) == 0


class TestASTPrettyPrinter:
    """Test AST pretty printing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.printer = ASTPrettyPrinter()
    
    def test_integer_node_printing(self):
        """Test printing integer nodes."""
        node = IntegerNode(42)
        result = self.printer.print_ast(node)
        assert result == "42"
    
    def test_identifier_node_printing(self):
        """Test printing identifier nodes."""
        node = IdentifierNode("variable")
        result = self.printer.print_ast(node)
        assert result == "variable"
    
    def test_simple_binary_op_printing(self):
        """Test printing simple binary operations."""
        left = IntegerNode(10)
        right = IntegerNode(5)
        node = BinaryOpNode(left, "+", right)
        
        result = self.printer.print_ast(node)
        assert result == "10 + 5"
    
    def test_assignment_printing(self):
        """Test printing assignment statements."""
        expression = IntegerNode(42)
        node = AssignmentNode("x", expression)
        
        result = self.printer.print_ast(node)
        assert result == "x = 42"
    
    def test_print_statement_printing(self):
        """Test printing print statements."""
        node = PrintNode("result")
        result = self.printer.print_ast(node)
        assert result == "print result"
    
    def test_complex_expression_printing(self):
        """Test printing complex nested expressions."""
        # Create: x + y * 2
        x = IdentifierNode("x")
        y = IdentifierNode("y")
        two = IntegerNode(2)
        multiply = BinaryOpNode(y, "*", two)
        add = BinaryOpNode(x, "+", multiply)
        
        result = self.printer.print_ast(add)
        assert result == "x + y * 2"
    
    def test_precedence_with_parentheses(self):
        """Test that precedence is handled correctly with parentheses."""
        # Create: (x + y) * 2
        x = IdentifierNode("x")
        y = IdentifierNode("y")
        two = IntegerNode(2)
        add = BinaryOpNode(x, "+", y)
        multiply = BinaryOpNode(add, "*", two)
        
        result = self.printer.print_ast(multiply)
        assert result == "(x + y) * 2"
    
    def test_right_associativity_parentheses(self):
        """Test that right associativity is handled correctly."""
        # Create: 10 - (5 - 2) which should print as 10 - (5 - 2)
        ten = IntegerNode(10)
        five = IntegerNode(5)
        two = IntegerNode(2)
        right_sub = BinaryOpNode(five, "-", two)
        left_sub = BinaryOpNode(ten, "-", right_sub)
        
        result = self.printer.print_ast(left_sub)
        assert result == "10 - (5 - 2)"
    
    def test_assignment_with_complex_expression(self):
        """Test printing assignment with complex expressions."""
        # Create: result = x + y * 2
        x = IdentifierNode("x")
        y = IdentifierNode("y")
        two = IntegerNode(2)
        multiply = BinaryOpNode(y, "*", two)
        add = BinaryOpNode(x, "+", multiply)
        assignment = AssignmentNode("result", add)
        
        result = self.printer.print_ast(assignment)
        assert result == "result = x + y * 2"
    
    def test_program_printing(self):
        """Test printing multiple statements as a program."""
        # Create program:
        # x = 10
        # y = x + 5
        # print y
        
        statements = [
            AssignmentNode("x", IntegerNode(10)),
            AssignmentNode("y", BinaryOpNode(IdentifierNode("x"), "+", IntegerNode(5))),
            PrintNode("y")
        ]
        
        result = self.printer.print_program(statements)
        expected = "x = 10\ny = x + 5\nprint y"
        assert result == expected
    
    def test_empty_program_printing(self):
        """Test printing empty program."""
        result = self.printer.print_program([])
        assert result == ""


class TestASTVisitorPattern:
    """Test that the visitor pattern works correctly."""
    
    def test_visitor_pattern_integer(self):
        """Test visitor pattern with integer nodes."""
        printer = ASTPrettyPrinter()
        node = IntegerNode(42)
        
        # Test that accept calls the correct visitor method
        result = node.accept(printer)
        assert result == "42"
    
    def test_visitor_pattern_identifier(self):
        """Test visitor pattern with identifier nodes."""
        printer = ASTPrettyPrinter()
        node = IdentifierNode("test")
        
        result = node.accept(printer)
        assert result == "test"
    
    def test_visitor_pattern_binary_op(self):
        """Test visitor pattern with binary operation nodes."""
        printer = ASTPrettyPrinter()
        left = IntegerNode(1)
        right = IntegerNode(2)
        node = BinaryOpNode(left, "+", right)
        
        result = node.accept(printer)
        assert result == "1 + 2"
    
    def test_visitor_pattern_assignment(self):
        """Test visitor pattern with assignment nodes."""
        printer = ASTPrettyPrinter()
        expression = IntegerNode(100)
        node = AssignmentNode("var", expression)
        
        result = node.accept(printer)
        assert result == "var = 100"
    
    def test_visitor_pattern_print(self):
        """Test visitor pattern with print nodes."""
        printer = ASTPrettyPrinter()
        node = PrintNode("output")
        
        result = node.accept(printer)
        assert result == "print output"


class TestASTNodeHierarchy:
    """Test AST node hierarchy and relationships."""
    
    def test_all_nodes_are_ast_nodes(self):
        """Test that all node types inherit from ASTNode."""
        nodes = [
            IntegerNode(1),
            IdentifierNode("x"),
            BinaryOpNode(IntegerNode(1), "+", IntegerNode(2)),
            AssignmentNode("x", IntegerNode(1)),
            PrintNode("x")
        ]
        
        for node in nodes:
            assert isinstance(node, ASTNode)
    
    def test_expression_nodes(self):
        """Test that expression nodes can be used interchangeably."""
        # All these should be valid expression nodes
        expressions = [
            IntegerNode(42),
            IdentifierNode("variable"),
            BinaryOpNode(IntegerNode(1), "+", IntegerNode(2))
        ]
        
        # Test that they can all be used as expressions in assignments
        for expr in expressions:
            assignment = AssignmentNode("test", expr)
            assert assignment.expression == expr
    
    def test_nested_expressions(self):
        """Test deeply nested expressions."""
        # Create: ((1 + 2) * 3) + 4
        one = IntegerNode(1)
        two = IntegerNode(2)
        three = IntegerNode(3)
        four = IntegerNode(4)
        
        add1 = BinaryOpNode(one, "+", two)
        mult = BinaryOpNode(add1, "*", three)
        add2 = BinaryOpNode(mult, "+", four)
        
        # Test that all children are properly connected
        assert len(add2.get_children()) == 2
        assert add2.left == mult
        assert add2.right == four
        
        assert len(mult.get_children()) == 2
        assert mult.left == add1
        assert mult.right == three
        
        assert len(add1.get_children()) == 2
        assert add1.left == one
        assert add1.right == two