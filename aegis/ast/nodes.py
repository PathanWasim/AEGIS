"""
AST node definitions for the AEGIS system.

This module defines all Abstract Syntax Tree node types used to represent
parsed AEGIS programs. Each node type corresponds to a language construct
and supports the visitor pattern for traversal and manipulation.

Supported nodes:
    - AssignmentNode  : x = expression
    - PrintNode       : print expression
    - IfNode          : if condition ... [else ...] end
    - WhileNode       : while condition ... end
    - BinaryOpNode    : left OP right  (arithmetic OR comparison)
    - IdentifierNode  : variable reference
    - IntegerNode     : integer literal
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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
        """Accept a visitor for the visitor pattern."""
        pass

    @abstractmethod
    def get_children(self) -> List['ASTNode']:
        """Return all child nodes of this AST node."""
        pass


# ---------------------------------------------------------------------------
# Expression nodes
# ---------------------------------------------------------------------------

@dataclass
class IntegerNode(ASTNode):
    """Represents an integer literal, e.g. 42"""
    value: int

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_integer(self)

    def get_children(self) -> List[ASTNode]:
        return []


@dataclass
class IdentifierNode(ASTNode):
    """Represents a variable reference, e.g. x, counter"""
    name: str

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_identifier(self)

    def get_children(self) -> List[ASTNode]:
        return []


@dataclass
class BinaryOpNode(ASTNode):
    """
    Represents a binary operation: left OP right.

    Arithmetic:  +, -, *, /, %
    Comparison:  >, <, >=, <=, ==, !=
    """
    left: 'ExpressionNode'
    operator: str
    right: 'ExpressionNode'

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_binary_op(self)

    def get_children(self) -> List[ASTNode]:
        return [self.left, self.right]


# ---------------------------------------------------------------------------
# Statement nodes
# ---------------------------------------------------------------------------

@dataclass
class AssignmentNode(ASTNode):
    """Represents a variable assignment: identifier = expression"""
    identifier: str
    expression: 'ExpressionNode'

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_assignment(self)

    def get_children(self) -> List[ASTNode]:
        return [self.expression]


@dataclass
class PrintNode(ASTNode):
    """
    Represents a print statement: print <expression>

    The expression can be any valid expression (variable, arithmetic,
    comparison), not just a bare identifier.
    """
    expression: 'ExpressionNode'

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_print(self)

    def get_children(self) -> List[ASTNode]:
        return [self.expression]


@dataclass
class IfNode(ASTNode):
    """
    Represents an if/else control flow statement:

        if <condition>
            <then_body>
        else          # optional
            <else_body>
        end
    """
    condition: 'ExpressionNode'
    then_body: List[ASTNode]
    else_body: List[ASTNode] = field(default_factory=list)

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_if(self)

    def get_children(self) -> List[ASTNode]:
        children = [self.condition] + self.then_body
        if self.else_body:
            children += self.else_body
        return children


@dataclass
class WhileNode(ASTNode):
    """
    Represents a while loop:

        while <condition>
            <body>
        end
    """
    condition: 'ExpressionNode'
    body: List[ASTNode]

    def accept(self, visitor: 'ASTVisitor') -> Any:
        return visitor.visit_while(self)

    def get_children(self) -> List[ASTNode]:
        return [self.condition] + self.body


# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

# Any node that can appear in expression position
ExpressionNode = BinaryOpNode | IdentifierNode | IntegerNode