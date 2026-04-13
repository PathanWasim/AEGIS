"""
AST → JSON serializer for the AEGIS API.

Converts an AST node tree into a plain dict structure that can be
sent over HTTP and rendered by the React ASTViewer component.
"""
from typing import Any, Dict, List
from .nodes import (
    ASTNode, AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode, IfNode, WhileNode
)


def ast_to_dict(nodes: List[ASTNode]) -> List[Dict[str, Any]]:
    """Convert a list of top-level AST nodes to JSON-serialisable dicts."""
    return [_node(n) for n in nodes]


def _node(n: ASTNode) -> Dict[str, Any]:
    if isinstance(n, AssignmentNode):
        name = n.identifier if isinstance(n.identifier, str) else n.identifier.name
        return {
            "type": "Assignment",
            "label": f"{name} =",
            "color": "statement",
            "children": [_node(n.expression)],
        }
    if isinstance(n, PrintNode):
        return {
            "type": "Print",
            "label": "print",
            "color": "keyword",
            "children": [_node(n.expression)],
        }
    if isinstance(n, IfNode):
        children = [{"type": "Condition", "label": "condition", "color": "control",
                     "children": [_node(n.condition)]}]
        children.append({"type": "Then", "label": "then", "color": "control",
                          "children": [_node(s) for s in n.then_body]})
        if n.else_body:
            children.append({"type": "Else", "label": "else", "color": "control",
                              "children": [_node(s) for s in n.else_body]})
        return {"type": "If", "label": "if", "color": "control", "children": children}
    if isinstance(n, WhileNode):
        return {
            "type": "While",
            "label": "while",
            "color": "control",
            "children": [
                {"type": "Condition", "label": "condition", "color": "control",
                 "children": [_node(n.condition)]},
                {"type": "Body", "label": "body", "color": "control",
                 "children": [_node(s) for s in n.body]},
            ],
        }
    if isinstance(n, BinaryOpNode):
        return {
            "type": "BinaryOp",
            "label": n.operator,
            "color": "operator",
            "children": [_node(n.left), _node(n.right)],
        }
    if isinstance(n, IdentifierNode):
        return {"type": "Identifier", "label": n.name, "color": "identifier", "children": []}
    if isinstance(n, IntegerNode):
        return {"type": "Integer", "label": str(n.value), "color": "literal", "children": []}
    return {"type": "Unknown", "label": str(n), "color": "unknown", "children": []}
