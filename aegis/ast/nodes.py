"""
AST node definitions for the AEGIS system.

This module defines all Abstract Syntax Tree node types used to represent
parsed AEGIS programs. Each node type corresponds to a language construct
and supports the visitor pattern for traversal and manipulation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .visitor import ASTVisitor


class ASTNode(ABC):
    """
    Base class for all AST nodes in the AEGIS system.
    
    All AST nodes must support the visitor pattern to enable
    different operations (interpretation, compilation, analysis)
    to be performed on the tree structure.
    """
    
    @abstractmethod
    def accept(self, visitor: 'ASTVisitor') -> Any:
        """
        Accept a visitor for the visitor pattern.
        
        Args:
            visitor: The visitor to accept
            
        Returns:
            Result of the visitor's operation on this node
        """
        pass
    
    @abstractmethod
    def get_children(self) -> List['ASTNode']:
        """
        Get all child nodes of this AST node.
        
        Returns:
            List of child nodes (empty for leaf nodes)
        """
        pass


@dataclass
class AssignmentNode(ASTNode):
    """
    Represents a variable assignment statement: identifier = expression
    
    Example: x = 10, y = x + 5
    """
    identifier: str
    expression: 'ExpressionNode'
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_assignment(self)
    
    def get_children(self) -> List[ASTNode]:
        return [self.expression]


@dataclass
class BinaryOpNode(ASTNode):
    """
    Represents a binary arithmetic operation: left operator right
    
    Example: x + 5, y * 2, a - b
    Supports operators: +, -, *, /
    """
    left: 'ExpressionNode'
    operator: str
    right: 'ExpressionNode'
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_binary_op(self)
    
    def get_children(self) -> List[ASTNode]:
        return [self.left, self.right]


@dataclass
class IdentifierNode(ASTNode):
    """
    Represents a variable reference.
    
    Example: x, variable_name, counter
    """
    name: str
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_identifier(self)
    
    def get_children(self) -> List[ASTNode]:
        return []


@dataclass
class IntegerNode(ASTNode):
    """
    Represents an integer literal.
    
    Example: 42, 0, -15
    """
    value: int
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_integer(self)
    
    def get_children(self) -> List[ASTNode]:
        return []


@dataclass
class PrintNode(ASTNode):
    """
    Represents a print statement: print identifier
    
    Example: print x, print result
    """
    identifier: str
    
    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_print(self)
    
    def get_children(self) -> List[ASTNode]:
        return []


# Type alias for expression nodes (nodes that can appear in expressions)
ExpressionNode = BinaryOpNode | IdentifierNode | IntegerNode