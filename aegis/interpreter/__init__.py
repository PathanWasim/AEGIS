"""
Interpreter module for AEGIS - Sandboxed execution environment.
"""

from .interpreter import SandboxedInterpreter
from .context import ExecutionContext, ExecutionMode
from .static_analyzer import StaticAnalyzer
from ..errors import SemanticError, RuntimeError as AegisRuntimeError

# Aliases for backward compatibility
AnalysisError = SemanticError
InterpreterError = AegisRuntimeError

__all__ = [
    'SandboxedInterpreter', 'ExecutionContext', 'ExecutionMode', 'StaticAnalyzer',
    'AnalysisError', 'InterpreterError', 'SemanticError', 'AegisRuntimeError'
]