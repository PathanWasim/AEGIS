"""
Execution context management for the AEGIS interpreter.

This module defines the ExecutionContext class that maintains the runtime
state during program execution, including variable storage and execution mode.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List


class ExecutionMode(Enum):
    """
    Enumeration of execution modes in the AEGIS system.
    
    INTERPRETED: Default sandboxed execution mode
    OPTIMIZED: Trusted code execution with performance optimizations
    """
    INTERPRETED = auto()
    OPTIMIZED = auto()


@dataclass
class ExecutionContext:
    """
    Maintains the runtime execution state for AEGIS programs.
    
    The execution context encapsulates all mutable state during program
    execution, enabling clean isolation between different program runs
    and supporting rollback operations when security violations occur.
    """
    variables: Dict[str, int] = field(default_factory=dict)
    execution_mode: ExecutionMode = ExecutionMode.INTERPRETED
    code_hash: str = ""
    output_buffer: List[str] = field(default_factory=list)
    
    def get_variable(self, name: str) -> int:
        """
        Retrieve the value of a variable.
        
        Args:
            name: Variable name to retrieve
            
        Returns:
            Current value of the variable
            
        Raises:
            KeyError: If variable is not defined
        """
        if name not in self.variables:
            raise KeyError(f"Undefined variable: {name}")
        return self.variables[name]
    
    def set_variable(self, name: str, value: int) -> None:
        """
        Set the value of a variable.
        
        Args:
            name: Variable name to set
            value: Integer value to assign
        """
        self.variables[name] = value
    
    def is_variable_defined(self, name: str) -> bool:
        """
        Check if a variable is defined in the current context.
        
        Args:
            name: Variable name to check
            
        Returns:
            True if variable is defined, False otherwise
        """
        return name in self.variables
    
    def add_output(self, text: str) -> None:
        """
        Add text to the output buffer.
        
        Args:
            text: Text to add to output
        """
        self.output_buffer.append(text)
    
    def get_output(self) -> str:
        """
        Get all output as a single string.
        
        Returns:
            Concatenated output with newlines
        """
        return '\n'.join(self.output_buffer)
    
    def clear_output(self) -> None:
        """Clear the output buffer."""
        self.output_buffer.clear()
    
    def reset(self) -> None:
        """
        Reset the execution context to initial state.
        
        This is used between program executions to ensure isolation.
        """
        self.variables.clear()
        self.output_buffer.clear()
        self.execution_mode = ExecutionMode.INTERPRETED
        self.code_hash = ""