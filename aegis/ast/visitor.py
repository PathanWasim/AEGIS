"""
Visitor pattern implementation for AST traversal - placeholder.
"""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .nodes import (
        AssignmentNode, BinaryOpNode, IdentifierNode, 
        IntegerNode, PrintNode
    )


class ASTVisitor(ABC):
    """
    Abstract base class for AST visitors.
    
    This is a placeholder implementation that will be completed with the AST.
    """
    
    @abstractmethod
    def visit_assignment(self, node: 'AssignmentNode') -> Any:
        """Visit an assignment node."""
        pass
    
    @abstractmethod
    def visit_binary_op(self, node: 'BinaryOpNode') -> Any:
        """Visit a binary operation node."""
        pass
    
    @abstractmethod
    def visit_identifier(self, node: 'IdentifierNode') -> Any:
        """Visit an identifier node."""
        pass
    
    @abstractmethod
    def visit_integer(self, node: 'IntegerNode') -> Any:
        """Visit an integer node."""
        pass
    
    @abstractmethod
    def visit_print(self, node: 'PrintNode') -> Any:
        """Visit a print node."""
        pass