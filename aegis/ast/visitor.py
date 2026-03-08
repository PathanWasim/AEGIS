"""
Visitor pattern abstract base class for AST traversal.

All AST visitors must implement a visit method for every node type.
"""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .nodes import (
        AssignmentNode, BinaryOpNode, IdentifierNode,
        IntegerNode, PrintNode, IfNode, WhileNode
    )


class ASTVisitor(ABC):
    """Abstract base class for AST visitors."""

    @abstractmethod
    def visit_assignment(self, node: 'AssignmentNode') -> Any:
        """Visit an assignment node."""
        pass

    @abstractmethod
    def visit_binary_op(self, node: 'BinaryOpNode') -> Any:
        """Visit a binary operation node (arithmetic or comparison)."""
        pass

    @abstractmethod
    def visit_identifier(self, node: 'IdentifierNode') -> Any:
        """Visit an identifier (variable reference) node."""
        pass

    @abstractmethod
    def visit_integer(self, node: 'IntegerNode') -> Any:
        """Visit an integer literal node."""
        pass

    @abstractmethod
    def visit_print(self, node: 'PrintNode') -> Any:
        """Visit a print statement node."""
        pass

    @abstractmethod
    def visit_if(self, node: 'IfNode') -> Any:
        """Visit an if/else control flow node."""
        pass

    @abstractmethod
    def visit_while(self, node: 'WhileNode') -> Any:
        """Visit a while loop node."""
        pass