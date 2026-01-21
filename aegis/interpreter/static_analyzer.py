"""
Static security analyzer implementation for AEGIS.

This module performs compile-time security and safety checks on the AST
before execution. The analyzer detects potential security issues and
prevents unsafe code from running.
"""

from typing import List, Set, Dict, Any
from ..ast.nodes import (
    ASTNode, AssignmentNode, BinaryOpNode, IdentifierNode,
    IntegerNode, PrintNode
)
from ..ast.visitor import ASTVisitor


class AnalysisError(Exception):
    """
    Exception raised for static analysis violations.
    
    Includes detailed information about the security issue detected.
    """
    
    def __init__(self, message: str, node: ASTNode = None):
        self.message = message
        self.node = node
        super().__init__(f"Static analysis error: {message}")


class StaticAnalyzer(ASTVisitor):
    """
    Static security analyzer for AEGIS programs.
    
    This analyzer performs compile-time checks to ensure program safety:
    - Undefined variable detection
    - Arithmetic safety validation
    - Expression well-formedness checking
    - Variable definition order validation
    
    The analyzer uses the visitor pattern to traverse the AST and
    maintains state about defined variables and potential issues.
    """
    
    def __init__(self):
        """Initialize the static analyzer."""
        self.defined_variables: Set[str] = set()
        self.used_variables: Set[str] = set()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.expression_depth = 0
        self.max_expression_depth = 10  # Prevent stack overflow
    
    def analyze(self, ast: List[ASTNode]) -> bool:
        """
        Perform static security analysis on the AST.
        
        Args:
            ast: List of AST nodes to analyze
            
        Returns:
            True if analysis passes, False if violations found
            
        Raises:
            AnalysisError: If critical security violations are detected
        """
        self.defined_variables.clear()
        self.used_variables.clear()
        self.errors.clear()
        self.warnings.clear()
        self.expression_depth = 0
        
        # Analyze each statement in order
        for node in ast:
            try:
                node.accept(self)
            except Exception as e:
                self.errors.append(f"Analysis failed for node {type(node).__name__}: {str(e)}")
        
        # Check for undefined variables (this is now handled in visit_identifier)
        # undefined_vars = self.used_variables - self.defined_variables
        # if undefined_vars:
        #     for var in sorted(undefined_vars):
        #         self.errors.append(f"Undefined variable: {var}")
        
        # If there are errors, raise exception
        if self.errors:
            error_msg = "; ".join(self.errors)
            raise AnalysisError(error_msg)
        
        return True
    
    def get_analysis_report(self) -> Dict[str, Any]:
        """
        Get detailed analysis report.
        
        Returns:
            Dictionary containing analysis results and statistics
        """
        return {
            'passed': len(self.errors) == 0,
            'errors': self.errors.copy(),
            'warnings': self.warnings.copy(),
            'defined_variables': sorted(self.defined_variables),
            'used_variables': sorted(self.used_variables),
            'undefined_variables': sorted(self.used_variables - self.defined_variables)
        }
    
    def visit_assignment(self, node: AssignmentNode) -> Any:
        """
        Analyze assignment statements.
        
        Checks:
        - Expression safety on right-hand side
        - Adds variable to defined set
        """
        # Analyze the expression first (before marking variable as defined)
        node.expression.accept(self)
        
        # Mark variable as defined AFTER analyzing the expression
        # This ensures self-referential assignments are caught
        self.defined_variables.add(node.identifier)
        
        return None
    
    def visit_binary_op(self, node: BinaryOpNode) -> Any:
        """
        Analyze binary operations.
        
        Checks:
        - Expression depth limits
        - Arithmetic safety (division by zero potential)
        - Operand validity
        """
        # Check expression depth to prevent stack overflow
        self.expression_depth += 1
        if self.expression_depth > self.max_expression_depth:
            self.errors.append(f"Expression too deeply nested (max depth: {self.max_expression_depth})")
            return None
        
        try:
            # Analyze left operand
            node.left.accept(self)
            
            # Analyze right operand
            node.right.accept(self)
            
            # Check for potential division by zero
            if node.operator == '/':
                if isinstance(node.right, IntegerNode) and node.right.value == 0:
                    self.errors.append("Division by zero detected")
                elif isinstance(node.right, IdentifierNode):
                    self.warnings.append(f"Potential division by zero with variable '{node.right.name}'")
            
            # Check for potential integer overflow (simplified check)
            if node.operator in ['*', '+']:
                if (isinstance(node.left, IntegerNode) and isinstance(node.right, IntegerNode)):
                    left_val = node.left.value
                    right_val = node.right.value
                    
                    if node.operator == '*' and (left_val > 1000000 or right_val > 1000000):
                        self.warnings.append("Potential integer overflow in multiplication")
                    elif node.operator == '+' and (left_val + right_val > 2147483647):
                        self.warnings.append("Potential integer overflow in addition")
        
        finally:
            self.expression_depth -= 1
        
        return None
    
    def visit_identifier(self, node: IdentifierNode) -> Any:
        """
        Analyze identifier references.
        
        Checks:
        - Marks variable as used
        - Variable name validity
        - Checks if variable is defined at this point
        """
        # Check if variable is defined at this point
        if node.name not in self.defined_variables:
            self.errors.append(f"Undefined variable: {node.name}")
        
        # Mark variable as used
        self.used_variables.add(node.name)
        
        # Check for valid identifier format (basic check)
        if not self._is_valid_identifier(node.name):
            self.errors.append(f"Invalid identifier format: {node.name}")
        
        return None
    
    def visit_integer(self, node: IntegerNode) -> Any:
        """
        Analyze integer literals.
        
        Checks:
        - Value range validation
        - Negative number handling
        """
        # Check for reasonable integer range
        if node.value < -2147483648 or node.value > 2147483647:
            self.warnings.append(f"Integer value {node.value} may cause overflow")
        
        return None
    
    def visit_print(self, node: PrintNode) -> Any:
        """
        Analyze print statements.
        
        Checks:
        - Variable existence (checked immediately)
        - Print statement validity
        """
        # Check if variable is defined at this point
        if node.identifier not in self.defined_variables:
            self.errors.append(f"Undefined variable: {node.identifier}")
        
        # Mark the printed variable as used
        self.used_variables.add(node.identifier)
        
        # Check for valid identifier format
        if not self._is_valid_identifier(node.identifier):
            self.errors.append(f"Invalid identifier in print statement: {node.identifier}")
        
        return None
    
    def _is_valid_identifier(self, name: str) -> bool:
        """
        Check if identifier name is valid.
        
        Args:
            name: Identifier name to validate
            
        Returns:
            True if identifier is valid
        """
        if not name:
            return False
        
        # Must start with letter or underscore
        if not (name[0].isalpha() or name[0] == '_'):
            return False
        
        # Rest must be alphanumeric or underscore
        for char in name[1:]:
            if not (char.isalnum() or char == '_'):
                return False
        
        # Cannot be a keyword
        if name in ['print']:
            return False
        
        return True
    
    def _check_undefined_variables(self, ast: List[ASTNode]) -> List[str]:
        """
        Check for undefined variable usage.
        
        Args:
            ast: List of AST nodes to check
            
        Returns:
            List of undefined variable names
        """
        # This is handled in the main analyze method
        return sorted(self.used_variables - self.defined_variables)
    
    def _check_arithmetic_safety(self, node: ASTNode) -> List[str]:
        """
        Check arithmetic operations for safety issues.
        
        Args:
            node: AST node to check
            
        Returns:
            List of safety issues found
        """
        issues = []
        
        if isinstance(node, BinaryOpNode):
            # Check for division by zero
            if node.operator == '/' and isinstance(node.right, IntegerNode):
                if node.right.value == 0:
                    issues.append("Division by zero")
            
            # Recursively check child nodes
            issues.extend(self._check_arithmetic_safety(node.left))
            issues.extend(self._check_arithmetic_safety(node.right))
        
        elif hasattr(node, 'get_children'):
            # Check all child nodes
            for child in node.get_children():
                issues.extend(self._check_arithmetic_safety(child))
        
        return issues
    
    def _validate_expression(self, node: ASTNode) -> bool:
        """
        Validate that an expression is well-formed.
        
        Args:
            node: Expression node to validate
            
        Returns:
            True if expression is well-formed
        """
        try:
            # Use the visitor pattern to validate
            node.accept(self)
            return True
        except Exception:
            return False