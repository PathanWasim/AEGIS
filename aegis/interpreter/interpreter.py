"""
Sandboxed interpreter implementation for AEGIS.

This module provides the secure execution environment for AEGIS programs.
The interpreter executes AST nodes in a sandboxed environment with safety
guarantees, overflow protection, and loop-iteration limits.

New in this version:
    - Supports if/else/end control flow  (IfNode)
    - Supports while/end loops           (WhileNode)
    - print prints any expression value  (not just identifiers)
    - Comparison operators produce 1 (true) / 0 (false) integers
    - Modulo operator support
    - Unary minus via 0-x BinaryOpNode pattern
"""

from typing import List, Any, Optional
from ..ast.nodes import (
    ASTNode, AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode, IfNode, WhileNode
)
from ..ast.visitor import ASTVisitor
from .context import ExecutionContext, ExecutionMode
from ..errors import RuntimeError as AegisRuntimeError


class SandboxedInterpreter(ASTVisitor):
    """
    Sandboxed interpreter for AEGIS programs.

    Security guarantees:
    - Complete memory isolation per execution
    - Integer overflow protection (32-bit range enforced)
    - No system call access
    - Runtime operation counting (prevents infinite loops)
    - Division-by-zero detection
    - Integrated runtime monitoring hooks
    """

    MAX_INTEGER = 2_147_483_647
    MIN_INTEGER = -2_147_483_648
    MAX_OPERATIONS = 50_000      # ~50 k ops per execution
    MAX_LOOP_ITERATIONS = 10_000 # per individual loop

    def __init__(self, runtime_monitor=None):
        """
        Initialise the sandboxed interpreter.

        Args:
            runtime_monitor: Optional monitor for tracking execution events.
        """
        self.operation_count = 0
        self.runtime_monitor = runtime_monitor

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------

    def execute(self, ast: List[ASTNode], context: ExecutionContext) -> None:
        """
        Execute a list of AST nodes (a complete program) in the sandboxed env.

        Args:
            ast:     List of top-level AST nodes.
            context: Execution context holding variable state and output.
        """
        self.operation_count = 0
        context.execution_mode = ExecutionMode.INTERPRETED
        self._current_context = context

        if self.runtime_monitor:
            self.runtime_monitor.start_monitoring(context)

        try:
            self._exec_block(ast)
        finally:
            if self.runtime_monitor:
                self.runtime_monitor.stop_monitoring()
            self._current_context = None

    # ------------------------------------------------------------------
    # Internal block executor
    # ------------------------------------------------------------------

    def _exec_block(self, statements: List[ASTNode]) -> None:
        """Execute a list of statements sequentially."""
        for node in statements:
            self._check_operation_limit()
            node.accept(self)

    # ------------------------------------------------------------------
    # Visitor implementations – statements
    # ------------------------------------------------------------------

    def visit_assignment(self, node: AssignmentNode) -> None:
        """Execute: identifier = expression"""
        context = self._require_context()
        self._check_operation_limit()

        if self.runtime_monitor:
            self.runtime_monitor.record_operation("assignment", node.identifier)

        value = node.expression.accept(self)
        self._assert_integer(value, "Assignment value")
        self._check_integer_bounds(value)

        identifier = node.identifier if isinstance(node.identifier, str) else node.identifier.name
        context.set_variable(identifier, value)

        if self.runtime_monitor:
            self.runtime_monitor.record_variable_access(identifier, "write")

    def visit_print(self, node: PrintNode) -> None:
        """Execute: print <expression>"""
        context = self._require_context()
        self._check_operation_limit()

        if self.runtime_monitor:
            self.runtime_monitor.record_operation("print", "expression")

        value = node.expression.accept(self)
        context.add_output(str(value))
        print(value)

    def visit_if(self, node: IfNode) -> None:
        """Execute: if condition ... [else ...] end"""
        self._check_operation_limit()
        condition_value = node.condition.accept(self)

        if condition_value:   # non-zero → truthy
            self._exec_block(node.then_body)
        elif node.else_body:
            self._exec_block(node.else_body)

    def visit_while(self, node: WhileNode) -> None:
        """Execute: while condition ... end"""
        context = self._require_context()
        iterations = 0

        while True:
            self._check_operation_limit()
            condition_value = node.condition.accept(self)
            if not condition_value:
                break

            iterations += 1
            if iterations > self.MAX_LOOP_ITERATIONS:
                raise AegisRuntimeError(
                    f"Loop iteration limit exceeded ({self.MAX_LOOP_ITERATIONS})",
                    execution_context=context,
                    variable_state=dict(context.variables),
                    suggestions=[
                        "Check loop condition — it may never become false",
                        f"Current iteration count: {iterations}",
                        "Consider restructuring the loop to terminate sooner"
                    ]
                )

            if self.runtime_monitor:
                self.runtime_monitor.record_operation("loop_iteration", f"iter={iterations}")

            self._exec_block(node.body)

    # ------------------------------------------------------------------
    # Visitor implementations – expressions
    # ------------------------------------------------------------------

    def visit_binary_op(self, node: BinaryOpNode) -> int:
        """Execute arithmetic or comparison binary operation."""
        context = self._require_context()
        self._check_operation_limit()

        left_val = node.left.accept(self)
        right_val = node.right.accept(self)

        self._assert_integer(left_val, "Left operand")
        self._assert_integer(right_val, "Right operand")

        op = node.operator

        # ---- Arithmetic ----
        if op == '+':
            result = left_val + right_val
        elif op == '-':
            result = left_val - right_val
        elif op == '*':
            result = left_val * right_val
        elif op == '/':
            if right_val == 0:
                raise AegisRuntimeError(
                    "Division by zero",
                    execution_context=context,
                    variable_state=dict(context.variables),
                    suggestions=[
                        "Ensure divisor is not zero before division",
                        "Add an if-check: if divisor == 0 ... end",
                    ]
                )
            result = left_val // right_val  # integer division
        elif op == '%':
            if right_val == 0:
                raise AegisRuntimeError(
                    "Modulo by zero",
                    execution_context=context,
                    variable_state=dict(context.variables),
                    suggestions=["Ensure modulo divisor is not zero"]
                )
            result = left_val % right_val

        # ---- Comparison  (return 1/0 as AEGIS ints) ----
        elif op == '>':
            result = 1 if left_val > right_val else 0
        elif op == '<':
            result = 1 if left_val < right_val else 0
        elif op == '>=':
            result = 1 if left_val >= right_val else 0
        elif op == '<=':
            result = 1 if left_val <= right_val else 0
        elif op == '==':
            result = 1 if left_val == right_val else 0
        elif op == '!=':
            result = 1 if left_val != right_val else 0
        else:
            raise AegisRuntimeError(
                f"Unknown operator: {op}",
                execution_context=context,
                variable_state=dict(context.variables)
            )

        if op in ('+', '-', '*', '/', '%'):
            self._check_integer_bounds(result)

        if self.runtime_monitor:
            self.runtime_monitor.record_arithmetic_operation(op, left_val, right_val, result)

        return result

    def visit_identifier(self, node: IdentifierNode) -> int:
        """Execute a variable lookup."""
        context = self._require_context()
        self._check_operation_limit()

        if self.runtime_monitor:
            self.runtime_monitor.record_variable_access(node.name, "read")

        try:
            return context.get_variable(node.name)
        except KeyError:
            available = list(context.variables.keys())
            raise AegisRuntimeError(
                f"Undefined variable: {node.name}",
                execution_context=context,
                variable_state=dict(context.variables),
                suggestions=[
                    f"Define '{node.name}' before using it",
                    "Check for typos in variable names",
                    f"Available variables: {available}" if available else "No variables defined yet"
                ]
            )

    def visit_integer(self, node: IntegerNode) -> int:
        """Return the integer literal value."""
        self._check_operation_limit()
        self._check_integer_bounds(node.value)

        if self.runtime_monitor:
            self.runtime_monitor.record_operation("literal", str(node.value))

        return node.value

    # ------------------------------------------------------------------
    # Safety helpers
    # ------------------------------------------------------------------

    def _require_context(self) -> ExecutionContext:
        ctx = getattr(self, '_current_context', None)
        if ctx is None:
            raise AegisRuntimeError(
                "No execution context — interpreter not properly initialised",
                execution_context=None,
                variable_state={}
            )
        return ctx

    def _check_operation_limit(self) -> None:
        """Increment and check the global operation counter."""
        self.operation_count += 1
        if self.operation_count > self.MAX_OPERATIONS:
            ctx = getattr(self, '_current_context', None)
            raise AegisRuntimeError(
                f"Operation limit exceeded ({self.MAX_OPERATIONS})",
                execution_context=ctx,
                variable_state=dict(ctx.variables) if ctx else {},
                suggestions=[
                    "Reduce program complexity",
                    "Check for infinite loops",
                    "Optimise expressions to reduce operation count"
                ]
            )

    def _check_integer_bounds(self, value: int) -> None:
        """Enforce 32-bit integer range."""
        if value < self.MIN_INTEGER or value > self.MAX_INTEGER:
            ctx = getattr(self, '_current_context', None)
            raise AegisRuntimeError(
                f"Integer overflow: {value} out of 32-bit range",
                execution_context=ctx,
                variable_state=dict(ctx.variables) if ctx else {}
            )

    def _assert_integer(self, value: Any, label: str) -> None:
        """Raise a runtime error if value is not an int."""
        if not isinstance(value, int):
            ctx = getattr(self, '_current_context', None)
            raise AegisRuntimeError(
                f"{label} must be integer, got {type(value).__name__}",
                execution_context=ctx,
                variable_state=dict(ctx.variables) if ctx else {}
            )

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------

    def get_operation_count(self) -> int:
        return self.operation_count

    def reset_operation_count(self) -> None:
        self.operation_count = 0

    def set_runtime_monitor(self, monitor) -> None:
        self.runtime_monitor = monitor