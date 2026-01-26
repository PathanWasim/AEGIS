"""
Comprehensive error handling system for AEGIS.

This module provides enhanced error reporting with categorization,
context information, and detailed diagnostic messages for all
components of the AEGIS system.
"""

from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


class ErrorCategory(Enum):
    """Categories of errors in the AEGIS system."""
    LEXICAL = "lexical"
    SYNTAX = "syntax"
    SEMANTIC = "semantic"
    RUNTIME = "runtime"
    SECURITY = "security"
    SYSTEM = "system"


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorContext:
    """
    Context information for enhanced error reporting.
    
    Provides detailed information about the execution state
    when an error occurred for better debugging and analysis.
    """
    source_code: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    token_value: Optional[str] = None
    variable_state: Optional[Dict[str, Any]] = None
    execution_mode: Optional[str] = None
    trust_score: Optional[float] = None
    instruction_count: Optional[int] = None
    stack_trace: Optional[List[str]] = None
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def get_source_line(self) -> Optional[str]:
        """Get the source code line where the error occurred."""
        if self.source_code and self.line:
            lines = self.source_code.split('\n')
            if 1 <= self.line <= len(lines):
                return lines[self.line - 1]
        return None
    
    def get_error_pointer(self) -> Optional[str]:
        """Get a pointer string showing the error location."""
        if self.column:
            return ' ' * (self.column - 1) + '^'
        return None


class AegisError(Exception):
    """
    Base class for all AEGIS errors with enhanced reporting.
    
    Provides comprehensive error information including categorization,
    severity, context, and suggestions for resolution.
    """
    
    def __init__(self, 
                 message: str,
                 category: ErrorCategory,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 context: Optional[ErrorContext] = None,
                 suggestions: Optional[List[str]] = None,
                 error_code: Optional[str] = None):
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.suggestions = suggestions or []
        self.error_code = error_code
        
        super().__init__(self._format_error_message())
    
    def _format_error_message(self) -> str:
        """Format a comprehensive error message."""
        parts = []
        
        # Error header with category and severity
        header = f"[{self.category.value.upper()}]"
        if self.severity != ErrorSeverity.ERROR:
            header += f" [{self.severity.value.upper()}]"
        if self.error_code:
            header += f" [{self.error_code}]"
        
        parts.append(header)
        parts.append(self.message)
        
        # Location information
        if self.context.line and self.context.column:
            parts.append(f"  at line {self.context.line}, column {self.context.column}")
        elif self.context.line:
            parts.append(f"  at line {self.context.line}")
        
        # Source code context
        source_line = self.context.get_source_line()
        if source_line:
            parts.append(f"  Source: {source_line.strip()}")
            pointer = self.context.get_error_pointer()
            if pointer:
                parts.append(f"          {pointer}")
        
        # Token information
        if self.context.token_value:
            parts.append(f"  Token: '{self.context.token_value}'")
        
        # Execution context
        if self.context.execution_mode:
            parts.append(f"  Execution mode: {self.context.execution_mode}")
        
        if self.context.trust_score is not None:
            parts.append(f"  Trust score: {self.context.trust_score:.2f}")
        
        if self.context.instruction_count is not None:
            parts.append(f"  Instructions executed: {self.context.instruction_count}")
        
        # Variable state (for runtime errors)
        if self.context.variable_state:
            var_info = ", ".join(f"{k}={v}" for k, v in self.context.variable_state.items())
            parts.append(f"  Variables: {var_info}")
        
        # Suggestions
        if self.suggestions:
            parts.append("  Suggestions:")
            for suggestion in self.suggestions:
                parts.append(f"    - {suggestion}")
        
        return "\n".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            'message': self.message,
            'category': self.category.value,
            'severity': self.severity.value,
            'error_code': self.error_code,
            'context': {
                'line': self.context.line,
                'column': self.context.column,
                'token_value': self.context.token_value,
                'execution_mode': self.context.execution_mode,
                'trust_score': self.context.trust_score,
                'instruction_count': self.context.instruction_count,
                'timestamp': self.context.timestamp.isoformat() if self.context.timestamp else None
            },
            'suggestions': self.suggestions
        }


class LexicalError(AegisError):
    """Enhanced lexical analysis error."""
    
    def __init__(self, message: str, line: int, column: int, 
                 char: Optional[str] = None, suggestions: Optional[List[str]] = None):
        context = ErrorContext(
            line=line,
            column=column,
            token_value=char
        )
        
        # Add default suggestions for common lexical errors
        default_suggestions = []
        if char and not char.isalnum() and char not in "=+-*/()":
            default_suggestions.append(f"Remove or replace the invalid character '{char}'")
        if "unexpected character" in message.lower():
            default_suggestions.append("Check for typos or unsupported characters")
        
        super().__init__(
            message=message,
            category=ErrorCategory.LEXICAL,
            context=context,
            suggestions=suggestions or default_suggestions,
            error_code="LEX001"
        )
    
    @property
    def line(self) -> Optional[int]:
        """Get line number for backward compatibility."""
        return self.context.line
    
    @property
    def column(self) -> Optional[int]:
        """Get column number for backward compatibility."""
        return self.context.column


class SyntaxError(AegisError):
    """Enhanced syntax analysis error."""
    
    def __init__(self, message: str, line: int, column: int,
                 token_value: Optional[str] = None, expected: Optional[str] = None,
                 suggestions: Optional[List[str]] = None):
        context = ErrorContext(
            line=line,
            column=column,
            token_value=token_value
        )
        
        # Add default suggestions for common syntax errors
        default_suggestions = []
        if expected:
            default_suggestions.append(f"Expected {expected}")
        if "unexpected token" in message.lower():
            default_suggestions.append("Check for missing operators or incorrect syntax")
        if token_value == "EOF":
            default_suggestions.append("Check for incomplete statements or missing tokens")
        
        super().__init__(
            message=message,
            category=ErrorCategory.SYNTAX,
            context=context,
            suggestions=suggestions or default_suggestions,
            error_code="SYN001"
        )
    
    @property
    def line(self) -> Optional[int]:
        """Get line number for backward compatibility."""
        return self.context.line
    
    @property
    def column(self) -> Optional[int]:
        """Get column number for backward compatibility."""
        return self.context.column
    
    @property
    def token(self):
        """Get token-like object for backward compatibility."""
        # Create a simple object with line and column attributes
        class TokenLike:
            def __init__(self, line, column, value):
                self.line = line
                self.column = column
                self.value = value
        
        return TokenLike(
            self.context.line,
            self.context.column,
            self.context.token_value
        )


class SemanticError(AegisError):
    """Enhanced semantic analysis error."""
    
    def __init__(self, message: str, variable: Optional[str] = None,
                 line: Optional[int] = None, suggestions: Optional[List[str]] = None):
        context = ErrorContext(
            line=line,
            token_value=variable
        )
        
        # Add default suggestions for common semantic errors
        default_suggestions = []
        if "undefined" in message.lower() and variable:
            default_suggestions.append(f"Define variable '{variable}' before using it")
            default_suggestions.append("Check for typos in variable names")
        if "overflow" in message.lower():
            default_suggestions.append("Use smaller numbers to avoid arithmetic overflow")
        
        super().__init__(
            message=message,
            category=ErrorCategory.SEMANTIC,
            context=context,
            suggestions=suggestions or default_suggestions,
            error_code="SEM001"
        )


class RuntimeError(AegisError):
    """Enhanced runtime execution error."""
    
    def __init__(self, message: str, execution_context=None,
                 variable_state: Optional[Dict[str, Any]] = None,
                 suggestions: Optional[List[str]] = None):
        context = ErrorContext(
            variable_state=variable_state,
            execution_mode=getattr(execution_context, 'mode', None) if execution_context else None,
            instruction_count=getattr(execution_context, 'instruction_count', None) if execution_context else None
        )
        
        # Add default suggestions for common runtime errors
        default_suggestions = []
        if "division by zero" in message.lower():
            default_suggestions.append("Ensure divisor is not zero before division")
        if "overflow" in message.lower():
            default_suggestions.append("Use smaller numbers or check arithmetic operations")
        
        super().__init__(
            message=message,
            category=ErrorCategory.RUNTIME,
            context=context,
            suggestions=suggestions or default_suggestions,
            error_code="RUN001"
        )


class SecurityError(AegisError):
    """Enhanced security violation error."""
    
    def __init__(self, message: str, violation_type: str,
                 execution_context=None, trust_score: Optional[float] = None,
                 suggestions: Optional[List[str]] = None):
        context = ErrorContext(
            execution_mode=getattr(execution_context, 'mode', None) if execution_context else None,
            trust_score=trust_score,
            instruction_count=getattr(execution_context, 'instruction_count', None) if execution_context else None
        )
        
        # Add default suggestions for security violations
        default_suggestions = []
        if "instruction_limit" in violation_type:
            default_suggestions.append("Reduce program complexity or increase instruction limit")
        if "memory_limit" in violation_type:
            default_suggestions.append("Reduce memory usage or increase memory limit")
        if "trust" in violation_type.lower():
            default_suggestions.append("Build trust through successful executions")
        
        super().__init__(
            message=f"Security violation ({violation_type}): {message}",
            category=ErrorCategory.SECURITY,
            severity=ErrorSeverity.CRITICAL,
            context=context,
            suggestions=suggestions or default_suggestions,
            error_code="SEC001"
        )


class SystemError(AegisError):
    """Enhanced system-level error."""
    
    def __init__(self, message: str, component: str,
                 suggestions: Optional[List[str]] = None):
        # Add default suggestions for system errors
        default_suggestions = []
        if "file" in message.lower():
            default_suggestions.append("Check file permissions and paths")
        if "memory" in message.lower():
            default_suggestions.append("Free up system memory or restart the application")
        
        super().__init__(
            message=f"System error in {component}: {message}",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            suggestions=suggestions or default_suggestions,
            error_code="SYS001"
        )


def format_error_summary(errors: List[AegisError]) -> str:
    """
    Format a summary of multiple errors for display.
    
    Args:
        errors: List of AEGIS errors
        
    Returns:
        Formatted error summary string
    """
    if not errors:
        return "No errors"
    
    summary = [f"Found {len(errors)} error(s):"]
    
    # Group by category
    by_category = {}
    for error in errors:
        category = error.category.value
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(error)
    
    # Display by category
    for category, category_errors in by_category.items():
        summary.append(f"\n{category.upper()} ERRORS ({len(category_errors)}):")
        for i, error in enumerate(category_errors, 1):
            summary.append(f"  {i}. {error.message}")
            if error.context.line:
                summary.append(f"     at line {error.context.line}")
    
    return "\n".join(summary)


def create_error_report(errors: List[AegisError]) -> Dict[str, Any]:
    """
    Create a structured error report for analysis.
    
    Args:
        errors: List of AEGIS errors
        
    Returns:
        Structured error report dictionary
    """
    return {
        'total_errors': len(errors),
        'by_category': {
            category.value: len([e for e in errors if e.category == category])
            for category in ErrorCategory
        },
        'by_severity': {
            severity.value: len([e for e in errors if e.severity == severity])
            for severity in ErrorSeverity
        },
        'errors': [error.to_dict() for error in errors],
        'timestamp': datetime.now().isoformat()
    }