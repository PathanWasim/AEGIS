"""
AEGIS Bytecode Compiler — converts AST → bytecode instruction list.

This is the code-generation phase of the AEGIS compiler pipeline.
It walks the AST and emits stack-machine instructions.

Pipeline:
    Source → Lexer → Parser → AST → BytecodeCompiler → [Instruction] → VM
"""
from typing import List, Optional
from ..ast.nodes import (
    ASTNode, AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode, IfNode, WhileNode
)
from ..ast.visitor import ASTVisitor
from .bytecode import Instruction, OpCode


class BytecodeCompiler(ASTVisitor):
    """
    Compiles an AEGIS AST into a flat list of bytecode instructions.

    Uses backpatching for forward jumps (if/while control flow).
    """

    def __init__(self):
        self._code: List[Instruction] = []

    # ── Public ────────────────────────────────────────────────────
    def compile(self, ast: List[ASTNode]) -> List[Instruction]:
        """Compile a list of top-level AST nodes to bytecode."""
        self._code = []
        for node in ast:
            node.accept(self)
        self._emit(OpCode.HALT)
        return self._code

    # ── Helpers ───────────────────────────────────────────────────
    def _emit(self, opcode: OpCode, arg=None, line: int = 0) -> int:
        """Append instruction, return its index (for backpatching)."""
        self._code.append(Instruction(opcode, arg, line))
        return len(self._code) - 1

    def _patch(self, idx: int, target: int) -> None:
        """Backpatch instruction at idx with jump target."""
        self._code[idx].arg = target

    def _current_offset(self) -> int:
        return len(self._code)

    # ── Visitor: statements ───────────────────────────────────────
    def visit_assignment(self, node: AssignmentNode) -> None:
        node.expression.accept(self)
        name = node.identifier if isinstance(node.identifier, str) else node.identifier.name
        self._emit(OpCode.STORE, name)

    def visit_print(self, node: PrintNode) -> None:
        node.expression.accept(self)
        self._emit(OpCode.PRINT)

    def visit_if(self, node: IfNode) -> None:
        # Compile condition
        node.condition.accept(self)
        # Emit conditional jump (to be patched)
        jump_false_idx = self._emit(OpCode.JUMP_IF_FALSE, None)

        # Compile then-body
        for stmt in node.then_body:
            stmt.accept(self)

        if node.else_body:
            # Jump over else-body after then-body
            jump_end_idx = self._emit(OpCode.JUMP, None)
            # Patch the false-jump to else-body start
            self._patch(jump_false_idx, self._current_offset())
            for stmt in node.else_body:
                stmt.accept(self)
            # Patch the end-jump
            self._patch(jump_end_idx, self._current_offset())
        else:
            # Patch the false-jump to after then-body
            self._patch(jump_false_idx, self._current_offset())

    def visit_while(self, node: WhileNode) -> None:
        loop_start = self._current_offset()
        # Compile condition
        node.condition.accept(self)
        # Emit conditional exit
        jump_false_idx = self._emit(OpCode.JUMP_IF_FALSE, None)
        # Compile body
        for stmt in node.body:
            stmt.accept(self)
        # Loop back
        self._emit(OpCode.JUMP, loop_start)
        # Patch exit jump
        self._patch(jump_false_idx, self._current_offset())

    # ── Visitor: expressions ──────────────────────────────────────
    def visit_binary_op(self, node: BinaryOpNode) -> None:
        node.left.accept(self)
        node.right.accept(self)
        op_map = {
            '+':  OpCode.ADD,
            '-':  OpCode.SUB,
            '*':  OpCode.MUL,
            '/':  OpCode.DIV,
            '%':  OpCode.MOD,
            '==': OpCode.EQ,
            '!=': OpCode.NEQ,
            '<':  OpCode.LT,
            '<=': OpCode.LTE,
            '>':  OpCode.GT,
            '>=': OpCode.GTE,
        }
        self._emit(op_map[node.operator])

    def visit_identifier(self, node: IdentifierNode) -> None:
        self._emit(OpCode.LOAD, node.name)

    def visit_integer(self, node: IntegerNode) -> None:
        self._emit(OpCode.PUSH, node.value)

    # ── Unused visitor stubs ──────────────────────────────────────
    def visit(self, node: ASTNode):
        return node.accept(self)
