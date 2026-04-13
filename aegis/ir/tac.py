"""
AEGIS Three-Address Code (TAC) / Intermediate Representation generator.

TAC is a classic compiler IR where every instruction has at most
3 addresses: result = operand1 OP operand2

Pipeline position:
    AST → TACGenerator → [TAC instructions] → (optimizer / bytecode compiler)
"""
from typing import List
from ..ast.nodes import (
    ASTNode, AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode, IfNode, WhileNode
)
from ..ast.visitor import ASTVisitor


class TACGenerator(ASTVisitor):
    """
    Converts an AEGIS AST to Three-Address Code strings.

    TAC instruction forms:
        t0 = a + b          (binary op, result to temp)
        x = t0              (copy/assignment)
        PRINT t0            (output)
        IF_FALSE t0 GOTO L1 (conditional jump)
        GOTO L0             (unconditional jump)
        L0:                 (label)
    """

    def __init__(self):
        self._instrs:    List[str] = []
        self._temp_id:   int = 0
        self._label_id:  int = 0

    # ── Public ────────────────────────────────────────────────────
    def generate(self, ast: List[ASTNode]) -> List[str]:
        self._instrs   = []
        self._temp_id  = 0
        self._label_id = 0
        for node in ast:
            node.accept(self)
        return self._instrs

    # ── Helpers ───────────────────────────────────────────────────
    def _new_temp(self) -> str:
        t = f"t{self._temp_id}"
        self._temp_id += 1
        return t

    def _new_label(self) -> str:
        lbl = f"L{self._label_id}"
        self._label_id += 1
        return lbl

    def _emit(self, s: str) -> None:
        self._instrs.append(s)

    # ── Visitors: statements ──────────────────────────────────────
    def visit_assignment(self, node: AssignmentNode) -> str:
        val = node.expression.accept(self)
        name = node.identifier if isinstance(node.identifier, str) else node.identifier.name
        self._emit(f"{name} = {val}")
        return name

    def visit_print(self, node: PrintNode) -> None:
        val = node.expression.accept(self)
        self._emit(f"PRINT {val}")

    def visit_if(self, node: IfNode) -> None:
        cond = node.condition.accept(self)
        label_else = self._new_label()
        label_end  = self._new_label()

        self._emit(f"IF_FALSE {cond} GOTO {label_else}")
        for stmt in node.then_body:
            stmt.accept(self)

        if node.else_body:
            self._emit(f"GOTO {label_end}")
            self._emit(f"{label_else}:")
            for stmt in node.else_body:
                stmt.accept(self)
            self._emit(f"{label_end}:")
        else:
            self._emit(f"{label_else}:")

    def visit_while(self, node: WhileNode) -> None:
        label_start = self._new_label()
        label_end   = self._new_label()

        self._emit(f"{label_start}:")
        cond = node.condition.accept(self)
        self._emit(f"IF_FALSE {cond} GOTO {label_end}")
        for stmt in node.body:
            stmt.accept(self)
        self._emit(f"GOTO {label_start}")
        self._emit(f"{label_end}:")

    # ── Visitors: expressions (return operand name) ───────────────
    def visit_binary_op(self, node: BinaryOpNode) -> str:
        left  = node.left.accept(self)
        right = node.right.accept(self)
        t = self._new_temp()
        self._emit(f"{t} = {left} {node.operator} {right}")
        return t

    def visit_identifier(self, node: IdentifierNode) -> str:
        return node.name

    def visit_integer(self, node: IntegerNode) -> str:
        return str(node.value)

    def visit(self, node: ASTNode):
        return node.accept(self)
