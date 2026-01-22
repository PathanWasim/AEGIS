"""
Sandboxed interpreter implementation for AEGIS.

This module provides the default secure execution environment for AEGIS programs.
The interpreter executes AST nodes in a completely sandboxed environment with
safety guarantees and overflow protection.
"""

from typing import List, Any, Optional
from ..ast.nodes import (
    ASTNode, AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode
)
from ..ast.visitor import ASTVisitor
from .context import ExecutionContext, ExecutionMode


class InterpreterError(Exception):
    """
    Exception raised for interpreter runtime errors.
    
    Includes context information for debugging and security analysis.
    """
    
    def __init__(self, message: str, context: ExecutionContext = None):
        self.message = message
        self.context = context
        super().__init__(f"Runtime error: {message}")


class SandboxedInterpreter(ASTVisitor):
    """
    Sandboxed interpreter for AEGIS programs.
    
    This interpreter provides the default secure execution environment:
    - Complete memory isolation per execution
    - Arithmetic overflow protection
    - No system call access
    - Controlled variable scoping
    - Safe error handling
    - Integrated runtime monitoring
    
    The interpreter uses the visitor pattern to execute AST nodes
    and maintains execution state in an ExecutionContext.
    """
    
    def __init__(self, runtime_monitor=None):
        """
        Initialize the sandboxed interpreter.
        
        Args:
            runtime_monitor: Optional runtime monitor for tracking execution
        """
        self.max_integer = 2147483647
        self.min_integer = -2147483648
        self.max_operations = 10000  # Prevent infinite loops
        self.operation_count = 0
        self.runtime_monitor = runtime_monitor
    
    def execute(self, ast: List[ASTNode], context: ExecutionContext) -> None:
        """
        Execute AST nodes in the sandboxed environment.
        
        Args:
            ast: List of AST nodes to execute
            context: Execution context for variable storage
            
        Raises:
            InterpreterError: If runtime errors occur
        """
        # Reset operation counter for this execution
        self.operation_count = 0
        
        # Ensure we're in interpreted mode
        context.execution_mode = ExecutionMode.INTERPRETED
        
        # Store context for visitor methods
        self._current_context = context
        
        # Start monitoring if available
        if self.runtime_monitor:
            self.runtime_monitor.start_monitoring(context)
        
        try:
            # Execute each statement in order
            for node in ast:
                self._check_operation_limit()
                node.accept(self)
        finally:
            # Stop monitoring and clean up context reference
            if self.runtime_monitor:
                self.runtime_monitor.stop_monitoring()
            self._current_context = None
    
    def visit_assignment(self, node: AssignmentNode) -> Any:
        """Execute assignment statements."""
        # Get context from the call
        context = getattr(self, '_current_context', None)
        if context is None:
            raise InterpreterError("No execution context available")
        
        self._check_operation_limit()
        
        # Record monitoring event
        if self.runtime_monitor:
            self.runtime_monitor.record_operation("assignment", f"{node.identifier} = <expression>")
        
        # Evaluate the expression
        value = node.expression.accept(self)
        
        # Validate the result
        if not isinstance(value, int):
            raise InterpreterError(f"Assignment value must be integer, got {type(value).__name__}")
        
        # Check for integer overflow
        self._check_integer_bounds(value)
        
        # Store the variable
        if isinstance(node.identifier, str):
            identifier_name = node.identifier
        else:
            identifier_name = node.identifier.name
            
        context.set_variable(identifier_name, value)
        
        # Record variable access
        if self.runtime_monitor:
            self.runtime_monitor.record_variable_access(identifier_name, "write")
        
        return None
    
    def visit_binary_op(self, node: BinaryOpNode) -> int:
        """Execute binary arithmetic operations."""
        context = getattr(self, '_current_context', None)
        if context is None:
            raise InterpreterError("No execution context available")
        
        self._check_operation_limit()
        
        # Evaluate operands
        left_val = node.left.accept(self)
        right_val = node.right.accept(self)
        
        # Validate operands
        if not isinstance(left_val, int) or not isinstance(right_val, int):
            raise InterpreterError(f"Arithmetic operands must be integers")
        
        # Perform operation with overflow protection
        try:
            if node.operator == '+':
                result = left_val + right_val
            elif node.operator == '-':
                result = left_val - right_val
            elif node.operator == '*':
                result = left_val * right_val
            elif node.operator == '/':
                if right_val == 0:
                    raise InterpreterError("Division by zero")
                # Integer division
                result = left_val // right_val
            else:
                raise InterpreterError(f"Unknown operator: {node.operator}")
            
            # Check for overflow
            self._check_integer_bounds(result)
            
            # Record monitoring event
            if self.runtime_monitor:
                self.runtime_monitor.record_arithmetic_operation(
                    node.operator, left_val, right_val, result
                )
            
            return result
            
        except OverflowError:
            raise InterpreterError("Integer overflow in arithmetic operation")
    
    def visit_identifier(self, node: IdentifierNode) -> int:
        """Execute identifier references (variable lookup)."""
        context = getattr(self, '_current_context', None)
        if context is None:
            raise InterpreterError("No execution context available")
        
        self._check_operation_limit()
        
        # Record variable access
        if self.runtime_monitor:
            self.runtime_monitor.record_variable_access(node.name, "read")
        
        try:
            return context.get_variable(node.name)
        except KeyError:
            raise InterpreterError(f"Undefined variable: {node.name}")
    
    def visit_integer(self, node: IntegerNode) -> int:
        """Execute integer literals."""
        self._check_operation_limit()
        
        # Validate integer bounds
        self._check_integer_bounds(node.value)
        
        # Record monitoring event
        if self.runtime_monitor:
            self.runtime_monitor.record_operation("literal", f"integer {node.value}")
        
        return node.value
    
    def visit_print(self, node: PrintNode) -> Any:
        """Execute print statements."""
        context = getattr(self, '_current_context', None)
        if context is None:
            raise InterpreterError("No execution context available")
        
        self._check_operation_limit()
        
        # Record monitoring event
        if self.runtime_monitor:
            self.runtime_monitor.record_operation("print", f"print {node.identifier}")
        
        try:
            # Get variable value
            value = context.get_variable(node.identifier)
            
            # Record variable access
            if self.runtime_monitor:
                self.runtime_monitor.record_variable_access(node.identifier, "read")
            
            # Add to output buffer
            context.add_output(str(value))
            
            # Also print to console for immediate feedback
            print(value)
            
        except KeyError:
            raise InterpreterError(f"Cannot print undefined variable: {node.identifier}")
        
        return None
    
    def _check_operation_limit(self) -> None:
        """
        Check if operation limit has been exceeded.
        
        Raises:
            InterpreterError: If too many operations have been performed
        """
        self.operation_count += 1
        if self.operation_count > self.max_operations:
            raise InterpreterError(f"Operation limit exceeded ({self.max_operations})")
    
    def _check_integer_bounds(self, value: int) -> None:
        """
        Check if integer value is within safe bounds.
        
        Args:
            value: Integer value to check
            
        Raises:
            InterpreterError: If value is out of bounds
        """
        if value < self.min_integer or value > self.max_integer:
            raise InterpreterError(f"Integer overflow: {value} is out of bounds")
    
    def get_operation_count(self) -> int:
        """
        Get the current operation count.
        
        Returns:
            Number of operations performed in current execution
        """
        return self.operation_count
    
    def reset_operation_count(self) -> None:
        """Reset the operation counter."""
        self.operation_count = 0
    
    def set_runtime_monitor(self, monitor) -> None:
        """Set the runtime monitor for this interpreter."""
        self.runtime_monitor = monitor