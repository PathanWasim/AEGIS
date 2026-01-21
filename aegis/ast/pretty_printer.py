"""
AST pretty printer implementation for converting AST back to source code.

This module provides the ASTPrettyPrinter class that implements the visitor
pattern to traverse AST nodes and generate equivalent source code. This is
crucial for round-trip testing and debugging.
"""

from typing import List
from .visitor import ASTVisitor
from .nodes import (
    AssignmentNode, BinaryOpNode, IdentifierNode, 
    IntegerNode, PrintNode, ASTNode
)


class ASTPrettyPrinter(ASTVisitor):
    """
    Pretty printer for AST nodes - converts AST back to source code.
    
    This class implements the visitor pattern to traverse AST nodes
    and generate equivalent AEGIS source code. The generated code
    should be semantically equivalent to the original program.
    
    The pretty printer handles:
    - Proper operator precedence with parentheses when needed
    - Consistent spacing and formatting
    - Multi-statement programs with newlines
    """
    
    def __init__(self):
        """Initialize the pretty printer."""
        self.indent_level = 0
        self.indent_size = 2
    
    def print_ast(self, node: ASTNode) -> str:
        """
        Convert an AST node back to source code.
        
        Args:
            node: The AST node to convert
            
        Returns:
            Source code representation of the AST
        """
        return node.accept(self)
    
    def print_program(self, statements: List[ASTNode]) -> str:
        """
        Convert a list of AST statements to a complete program.
        
        Args:
            statements: List of AST statement nodes
            
        Returns:
            Complete program source code
        """
        if not statements:
            return ""
        
        program_lines = []
        for statement in statements:
            line = statement.accept(self)
            program_lines.append(line)
        
        return '\n'.join(program_lines)
    
    def visit_assignment(self, node: AssignmentNode) -> str:
        """Visit an assignment node and generate assignment statement."""
        expression_str = node.expression.accept(self)
        return f"{node.identifier} = {expression_str}"
    
    def visit_binary_op(self, node: BinaryOpNode) -> str:
        """Visit a binary operation node and generate expression with proper precedence."""
        left_str = node.left.accept(self)
        right_str = node.right.accept(self)
        
        # Add parentheses for nested operations to ensure correct precedence
        # This is a simple approach - could be optimized to minimize parentheses
        if isinstance(node.left, BinaryOpNode):
            if self._needs_parentheses(node.left.operator, node.operator, True):
                left_str = f"({left_str})"
        
        if isinstance(node.right, BinaryOpNode):
            if self._needs_parentheses(node.right.operator, node.operator, False):
                right_str = f"({right_str})"
        
        return f"{left_str} {node.operator} {right_str}"
    
    def visit_identifier(self, node: IdentifierNode) -> str:
        """Visit an identifier node and return the variable name."""
        return node.name
    
    def visit_integer(self, node: IntegerNode) -> str:
        """Visit an integer node and return the numeric value."""
        return str(node.value)
    
    def visit_print(self, node: PrintNode) -> str:
        """Visit a print node and generate print statement."""
        return f"print {node.identifier}"
    
    def _needs_parentheses(self, inner_op: str, outer_op: str, is_left: bool) -> bool:
        """
        Determine if parentheses are needed for correct precedence.
        
        Args:
            inner_op: Operator of the inner (nested) expression
            outer_op: Operator of the outer expression
            is_left: True if inner expression is on the left side
            
        Returns:
            True if parentheses are needed
        """
        # Operator precedence: * / (higher) > + - (lower)
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
        
        inner_prec = precedence.get(inner_op, 0)
        outer_prec = precedence.get(outer_op, 0)
        
        # Need parentheses if inner has lower precedence
        if inner_prec < outer_prec:
            return True
        
        # For same precedence, need parentheses on right side for non-associative ops
        if inner_prec == outer_prec and not is_left and outer_op in ['-', '/']:
            return True
        
        return False
    
    def _get_indent(self) -> str:
        """Get the current indentation string."""
        return ' ' * (self.indent_level * self.indent_size)
    
    def _increase_indent(self) -> None:
        """Increase indentation level."""
        self.indent_level += 1
    
    def _decrease_indent(self) -> None:
        """Decrease indentation level."""
        self.indent_level = max(0, self.indent_level - 1)