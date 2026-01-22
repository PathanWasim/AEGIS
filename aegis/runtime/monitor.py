"""
Runtime monitoring implementation for AEGIS.

This module tracks execution behavior and detects security violations
in real-time during program execution. It provides metrics collection
and violation detection for the trust management system.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from ..interpreter.context import ExecutionContext


@dataclass
class ExecutionMetrics:
    """
    Tracks performance and behavior statistics during execution.
    
    This class maintains comprehensive metrics about program execution
    including operation counts, timing, and security-relevant events.
    """
    instruction_count: int = 0
    memory_usage: int = 0
    execution_time: float = 0.0
    operations_performed: List[str] = field(default_factory=list)
    violations_detected: List['SecurityViolation'] = field(default_factory=list)
    variables_accessed: List[str] = field(default_factory=list)
    arithmetic_operations: int = 0
    assignment_operations: int = 0
    print_operations: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Optimization-related metrics
    optimization_applied: bool = False
    cache_hit: bool = False
    speedup_factor: float = 1.0
    
    def add_operation(self, operation_type: str, details: str = "") -> None:
        """
        Record an operation performed during execution.
        
        Args:
            operation_type: Type of operation (assignment, arithmetic, print, etc.)
            details: Additional details about the operation
        """
        self.instruction_count += 1
        self.operations_performed.append(f"{operation_type}: {details}")
        
        # Update specific counters
        if operation_type == "arithmetic":
            self.arithmetic_operations += 1
        elif operation_type == "assignment":
            self.assignment_operations += 1
        elif operation_type == "print":
            self.print_operations += 1
    
    def add_variable_access(self, variable_name: str) -> None:
        """Record access to a variable."""
        if variable_name not in self.variables_accessed:
            self.variables_accessed.append(variable_name)
    
    def start_timing(self) -> None:
        """Start timing execution."""
        self.start_time = datetime.now()
    
    def end_timing(self) -> None:
        """End timing execution and calculate duration."""
        self.end_time = datetime.now()
        if self.start_time:
            delta = self.end_time - self.start_time
            self.execution_time = delta.total_seconds()
    
    def get_operations_per_second(self) -> float:
        """Calculate operations per second."""
        if self.execution_time > 0:
            return self.instruction_count / self.execution_time
        return 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for serialization."""
        return {
            'instruction_count': self.instruction_count,
            'memory_usage': self.memory_usage,
            'execution_time': self.execution_time,
            'operations_performed': len(self.operations_performed),
            'violations_detected': len(self.violations_detected),
            'variables_accessed': len(self.variables_accessed),
            'arithmetic_operations': self.arithmetic_operations,
            'assignment_operations': self.assignment_operations,
            'print_operations': self.print_operations,
            'operations_per_second': self.get_operations_per_second(),
            'optimization_applied': self.optimization_applied,
            'cache_hit': self.cache_hit,
            'speedup_factor': self.speedup_factor
        }


class SecurityViolation(Exception):
    """
    Exception raised for security violations detected during runtime.
    
    This exception includes detailed information about the violation
    for analysis and trust management decisions.
    """
    
    def __init__(self, violation_type: str, message: str, context: ExecutionContext = None):
        self.violation_type = violation_type
        self.message = message
        self.context = context
        self.timestamp = datetime.now()
        super().__init__(f"Security violation ({violation_type}): {message}")


class RuntimeMonitor:
    """
    Runtime monitor for AEGIS programs.
    
    This monitor tracks execution behavior in real-time and detects
    security violations. It provides comprehensive metrics collection
    and integrates with the trust management system.
    
    Key responsibilities:
    - Track execution metrics (instruction count, timing, memory)
    - Detect security violations (unauthorized operations, limits)
    - Provide real-time statistics to trust manager
    - Log execution events for audit purposes
    """
    
    def __init__(self):
        """Initialize the runtime monitor."""
        self.current_metrics: Optional[ExecutionMetrics] = None
        self.execution_history: List[ExecutionMetrics] = []
        self.violation_threshold = 1000  # Max instructions per execution
        self.memory_threshold = 1024 * 1024  # 1MB memory limit
        self.is_monitoring = False
        self.monitored_context: Optional[ExecutionContext] = None
        
        # Rollback integration
        self.rollback_callback: Optional[Callable[[List[SecurityViolation], str, str], None]] = None
        self.current_execution_mode = 'sandboxed'
        self.current_code_hash = None
    
    def register_rollback_callback(self, callback: Callable[[List[SecurityViolation], str, str], None]) -> None:
        """
        Register callback for rollback handling.
        
        Args:
            callback: Function to call when violations require rollback (violations, execution_mode, code_hash)
        """
        self.rollback_callback = callback
    
    def set_execution_mode(self, mode: str, code_hash: str = None) -> None:
        """
        Set current execution mode for rollback decisions.
        
        Args:
            mode: Execution mode ('sandboxed' or 'optimized')
            code_hash: Hash of code being executed
        """
        self.current_execution_mode = mode
        self.current_code_hash = code_hash
    
    def start_monitoring(self, execution_context: ExecutionContext) -> None:
        """
        Start monitoring an execution context.
        
        Args:
            execution_context: The context to monitor
        """
        self.current_metrics = ExecutionMetrics()
        self.current_metrics.start_timing()
        self.is_monitoring = True
        self.monitored_context = execution_context
        
        self.record_operation("monitor_start", "Execution monitoring started")
    
    def stop_monitoring(self) -> ExecutionMetrics:
        """
        Stop monitoring and return final metrics.
        
        Returns:
            Final execution metrics
        """
        if self.current_metrics:
            self.current_metrics.end_timing()
            self.record_operation("monitor_stop", "Execution monitoring stopped")
            
            # Archive metrics
            self.execution_history.append(self.current_metrics)
            
            # Keep only recent history (last 100 executions)
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]
        
        self.is_monitoring = False
        final_metrics = self.current_metrics
        self.current_metrics = None
        self.monitored_context = None
        
        return final_metrics or ExecutionMetrics()
    
    def record_operation(self, operation: str, details: str = "") -> None:
        """
        Record an operation performed during execution.
        
        Args:
            operation: Type of operation
            details: Additional details about the operation
        """
        if not self.is_monitoring or not self.current_metrics:
            return
        
        self.current_metrics.add_operation(operation, details)
        
        # Check for violations
        self._check_violations()
    
    def record_variable_access(self, variable_name: str, access_type: str) -> None:
        """
        Record access to a variable.
        
        Args:
            variable_name: Name of the variable accessed
            access_type: Type of access (read, write)
        """
        if not self.is_monitoring or not self.current_metrics:
            return
        
        self.current_metrics.add_variable_access(variable_name)
        self.record_operation("variable_access", f"{access_type} {variable_name}")
    
    def record_arithmetic_operation(self, operator: str, left: Any, right: Any, result: Any) -> None:
        """
        Record an arithmetic operation.
        
        Args:
            operator: The arithmetic operator
            left: Left operand
            right: Right operand  
            result: Operation result
        """
        if not self.is_monitoring:
            return
        
        details = f"{left} {operator} {right} = {result}"
        self.record_operation("arithmetic", details)
        
        # Check for potential overflow
        if isinstance(result, int) and (result > 2147483647 or result < -2147483648):
            self._raise_violation("arithmetic_overflow", f"Result {result} exceeds integer bounds")
    
    def check_violations(self) -> List[SecurityViolation]:
        """
        Check for security violations in current execution.
        
        Returns:
            List of detected violations
        """
        violations = []
        
        if not self.current_metrics:
            return violations
        
        # Check instruction count limit
        if self.current_metrics.instruction_count > self.violation_threshold:
            violation = SecurityViolation(
                "instruction_limit",
                f"Instruction count {self.current_metrics.instruction_count} exceeds limit {self.violation_threshold}",
                self.monitored_context
            )
            violations.append(violation)
        
        # Check memory usage (simulated)
        if self.current_metrics.memory_usage > self.memory_threshold:
            violation = SecurityViolation(
                "memory_limit",
                f"Memory usage {self.current_metrics.memory_usage} exceeds limit {self.memory_threshold}",
                self.monitored_context
            )
            violations.append(violation)
        
        return violations
    
    def get_metrics(self) -> ExecutionMetrics:
        """
        Get current execution metrics.
        
        Returns:
            Current metrics or empty metrics if not monitoring
        """
        return self.current_metrics or ExecutionMetrics()
    
    def get_execution_history(self) -> List[ExecutionMetrics]:
        """
        Get execution history.
        
        Returns:
            List of historical execution metrics
        """
        return self.execution_history.copy()
    
    def get_average_metrics(self) -> Dict[str, float]:
        """
        Get average metrics across execution history.
        
        Returns:
            Dictionary of average metric values
        """
        if not self.execution_history:
            return {}
        
        total_instructions = sum(m.instruction_count for m in self.execution_history)
        total_time = sum(m.execution_time for m in self.execution_history)
        total_violations = sum(len(m.violations_detected) for m in self.execution_history)
        
        count = len(self.execution_history)
        
        return {
            'avg_instruction_count': total_instructions / count,
            'avg_execution_time': total_time / count,
            'avg_violations_per_execution': total_violations / count,
            'total_executions': count
        }
    
    def _check_violations(self) -> None:
        """Internal method to check for violations and raise if found."""
        violations = self.check_violations()
        
        if violations:
            # Add violations to metrics
            if self.current_metrics:
                self.current_metrics.violations_detected.extend(violations)
            
            # Trigger rollback if in optimized mode and callback is registered
            if (self.rollback_callback and 
                self.current_execution_mode == 'optimized' and 
                self.current_code_hash):
                try:
                    self.rollback_callback(violations, self.current_execution_mode, self.current_code_hash)
                except Exception as e:
                    print(f"[MONITOR] Warning: Rollback callback failed - {e}")
            
            # Raise the first violation
            raise violations[0]
    
    def _raise_violation(self, violation_type: str, message: str) -> None:
        """
        Raise a security violation.
        
        Args:
            violation_type: Type of violation
            message: Violation message
        """
        violation = SecurityViolation(violation_type, message, self.monitored_context)
        
        if self.current_metrics:
            self.current_metrics.violations_detected.append(violation)
        
        # Trigger rollback if in optimized mode and callback is registered
        if (self.rollback_callback and 
            self.current_execution_mode == 'optimized' and 
            self.current_code_hash):
            try:
                self.rollback_callback([violation], self.current_execution_mode, self.current_code_hash)
            except Exception as e:
                print(f"[MONITOR] Warning: Rollback callback failed - {e}")
        
        raise violation
    
    def set_violation_threshold(self, threshold: int) -> None:
        """Set the instruction count violation threshold."""
        self.violation_threshold = threshold
    
    def set_memory_threshold(self, threshold: int) -> None:
        """Set the memory usage violation threshold."""
        self.memory_threshold = threshold