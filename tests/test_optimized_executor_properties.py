"""
Property-based tests for optimized execution system in AEGIS.

These tests validate that the optimized execution system maintains semantic
equivalence with the sandboxed interpreter while providing performance benefits.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from aegis.compiler.optimizer import OptimizedExecutor, ASTOptimizer
from aegis.compiler.cache import CodeCache
from aegis.interpreter.interpreter import SandboxedInterpreter
from aegis.interpreter.context import ExecutionContext
from aegis.runtime.monitor import RuntimeMonitor
from aegis.ast.nodes import AssignmentNode, BinaryOpNode, IdentifierNode, IntegerNode, PrintNode
from aegis.lexer.lexer import Lexer
from aegis.parser.parser import Parser
import tempfile
import os


class TestOptimizedExecutorProperties:
    """Property-based tests for optimized execution system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create fresh instances for each test to avoid state pollution
        self.cache = CodeCache()
        self.monitor = RuntimeMonitor()
        self.optimizer = OptimizedExecutor(self.cache, self.monitor)
        self.interpreter = SandboxedInterpreter(self.monitor)
    
    @given(st.integers(min_value=-1000, max_value=1000),
           st.integers(min_value=-1000, max_value=1000))
    @settings(max_examples=50, deadline=2000)
    def test_arithmetic_semantic_equivalence(self, left_val, right_val):
        """
        **Feature: aegis, Property 10a: Arithmetic Semantic Equivalence**
        
        The optimized executor must produce identical results to the sandboxed
        interpreter for all arithmetic operations, ensuring that optimizations
        preserve semantic correctness.
        
        **Validates: Requirements 8.4**
        """
        # Test all arithmetic operators
        operators = ['+', '-', '*']
        if right_val != 0:  # Avoid division by zero
            operators.append('/')
        
        for operator in operators:
            # Create AST for: result = left_val operator right_val
            ast = [
                AssignmentNode(
                    "result",
                    BinaryOpNode(IntegerNode(left_val), operator, IntegerNode(right_val))
                )
            ]
            
            # Execute with sandboxed interpreter
            context_interpreted = ExecutionContext()
            try:
                self.interpreter.execute(ast, context_interpreted)
                interpreted_result = context_interpreted.get_variable("result")
            except Exception as e:
                # If interpreter fails, optimized should fail the same way
                context_optimized = ExecutionContext()
                with pytest.raises(type(e)):
                    code_hash = f"arith_{left_val}_{operator}_{right_val}"
                    self.optimizer.execute_optimized(code_hash, ast, context_optimized)
                continue
            
            # Execute with optimized executor
            context_optimized = ExecutionContext()
            code_hash = f"arith_{left_val}_{operator}_{right_val}"
            
            try:
                metrics = self.optimizer.execute_optimized(code_hash, ast, context_optimized)
                optimized_result = context_optimized.get_variable("result")
                
                # Results must be identical
                assert optimized_result == interpreted_result, \
                    f"Semantic mismatch: {left_val} {operator} {right_val} = " \
                    f"interpreted: {interpreted_result}, optimized: {optimized_result}"
                
                # Optimized execution should be marked as such
                assert metrics.optimization_applied is True
                
            except Exception as e:
                # If optimized fails, it should be the same type of error
                pytest.fail(f"Optimized execution failed where interpreted succeeded: {e}")
    
    @given(st.lists(st.integers(min_value=0, max_value=100), min_size=1, max_size=5))
    @settings(max_examples=30, deadline=2000)
    def test_variable_assignment_semantic_equivalence(self, values):
        """
        **Feature: aegis, Property 10b: Variable Assignment Semantic Equivalence**
        
        The optimized executor must maintain identical variable state as the
        sandboxed interpreter for all assignment operations and sequences.
        
        **Validates: Requirements 8.4**
        """
        # Create a sequence of assignments: x0 = values[0], x1 = values[1], etc.
        ast = []
        variable_names = []
        
        for i, value in enumerate(values):
            var_name = f"x{i}"
            variable_names.append(var_name)
            ast.append(AssignmentNode(var_name, IntegerNode(value)))
        
        # Execute with sandboxed interpreter
        context_interpreted = ExecutionContext()
        self.interpreter.execute(ast, context_interpreted)
        
        # Execute with optimized executor
        context_optimized = ExecutionContext()
        code_hash = f"assignments_{hash(tuple(values))}"
        
        metrics = self.optimizer.execute_optimized(code_hash, ast, context_optimized)
        
        # All variables must have identical values
        for var_name in variable_names:
            interpreted_val = context_interpreted.get_variable(var_name)
            optimized_val = context_optimized.get_variable(var_name)
            
            assert optimized_val == interpreted_val, \
                f"Variable {var_name}: interpreted={interpreted_val}, optimized={optimized_val}"
        
        # Optimized execution should be marked as such
        assert metrics.optimization_applied is True
    
    @given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=8),
           st.integers(min_value=1, max_value=50))
    @settings(max_examples=20, deadline=2000)
    def test_complex_expression_semantic_equivalence(self, var_name, base_value):
        """
        **Feature: aegis, Property 10c: Complex Expression Semantic Equivalence**
        
        The optimized executor must produce identical results for complex
        expressions involving multiple operations and variables.
        
        **Validates: Requirements 8.4**
        """
        # Create complex expression: var = base_value; result = var + 2 * 3 - 1
        ast = [
            AssignmentNode(var_name, IntegerNode(base_value)),
            AssignmentNode(
                "result",
                BinaryOpNode(
                    IdentifierNode(var_name),
                    "+",
                    BinaryOpNode(
                        BinaryOpNode(IntegerNode(2), "*", IntegerNode(3)),
                        "-",
                        IntegerNode(1)
                    )
                )
            )
        ]
        
        # Execute with sandboxed interpreter
        context_interpreted = ExecutionContext()
        self.interpreter.execute(ast, context_interpreted)
        
        # Execute with optimized executor
        context_optimized = ExecutionContext()
        code_hash = f"complex_{var_name}_{base_value}"
        
        metrics = self.optimizer.execute_optimized(code_hash, ast, context_optimized)
        
        # Results must be identical
        interpreted_result = context_interpreted.get_variable("result")
        optimized_result = context_optimized.get_variable("result")
        
        assert optimized_result == interpreted_result, \
            f"Complex expression mismatch: interpreted={interpreted_result}, optimized={optimized_result}"
        
        # Both variables should have same values
        interpreted_var = context_interpreted.get_variable(var_name)
        optimized_var = context_optimized.get_variable(var_name)
        
        assert optimized_var == interpreted_var, \
            f"Variable {var_name}: interpreted={interpreted_var}, optimized={optimized_var}"
        
        # Optimized execution should be marked as such
        assert metrics.optimization_applied is True
    
    @given(st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=1, max_size=5), 
                   min_size=1, max_size=3))
    @settings(max_examples=15, deadline=2000)
    def test_print_output_semantic_equivalence(self, var_names):
        """
        **Feature: aegis, Property 10d: Print Output Semantic Equivalence**
        
        The optimized executor must produce identical console output as the
        sandboxed interpreter for all print operations.
        
        **Validates: Requirements 8.4**
        """
        # Make variable names unique
        unique_vars = list(set(var_names))
        assume(len(unique_vars) >= 1)
        
        # Create AST: assign values to variables, then print them
        ast = []
        expected_values = []
        
        for i, var_name in enumerate(unique_vars):
            value = (i + 1) * 10  # 10, 20, 30, etc.
            expected_values.append(value)
            ast.append(AssignmentNode(var_name, IntegerNode(value)))
            ast.append(PrintNode(var_name))
        
        # Execute with sandboxed interpreter
        context_interpreted = ExecutionContext()
        self.interpreter.execute(ast, context_interpreted)
        
        # Execute with optimized executor
        context_optimized = ExecutionContext()
        code_hash = f"print_{hash(tuple(unique_vars))}"
        
        metrics = self.optimizer.execute_optimized(code_hash, ast, context_optimized)
        
        # Output buffers must be identical
        interpreted_output = context_interpreted.output_buffer
        optimized_output = context_optimized.output_buffer
        
        assert optimized_output == interpreted_output, \
            f"Output mismatch: interpreted={interpreted_output}, optimized={optimized_output}"
        
        # Verify expected output content
        expected_output = [str(val) for val in expected_values]
        assert interpreted_output == expected_output, \
            f"Unexpected output: expected={expected_output}, got={interpreted_output}"
        
        # Optimized execution should be marked as such
        assert metrics.optimization_applied is True
    
    @given(st.integers(min_value=1, max_value=50),
           st.integers(min_value=1, max_value=50))
    @settings(max_examples=15, deadline=3000)
    def test_simple_program_semantic_equivalence(self, val1, val2):
        """
        **Feature: aegis, Property 10e: Simple Program Semantic Equivalence**
        
        The optimized executor must produce identical results to the sandboxed
        interpreter for simple AEGIS programs with assignments and arithmetic.
        
        **Validates: Requirements 8.4**
        """
        # Create a simple but realistic program
        source = f"""
        a = {val1}
        b = {val2}
        c = a + b
        d = c * 2
        print d
        """
        
        try:
            # Parse the source
            lexer = Lexer()
            tokens = lexer.tokenize(source)
            parser = Parser()
            ast = parser.parse(tokens)
            
            if len(ast) == 0:
                assume(False)  # Skip empty programs
            
        except Exception:
            assume(False)  # Skip invalid programs
        
        # Execute with sandboxed interpreter
        context_interpreted = ExecutionContext()
        try:
            self.interpreter.execute(ast, context_interpreted)
        except Exception:
            assume(False)  # Skip programs that fail in interpreter
        
        # Execute with optimized executor
        context_optimized = ExecutionContext()
        code_hash = f"simple_{val1}_{val2}"
        
        try:
            metrics = self.optimizer.execute_optimized(code_hash, ast, context_optimized)
            
            # All variables must have identical values
            for var_name in context_interpreted.variables:
                interpreted_val = context_interpreted.get_variable(var_name)
                optimized_val = context_optimized.get_variable(var_name)
                
                assert optimized_val == interpreted_val, \
                    f"Variable {var_name}: interpreted={interpreted_val}, optimized={optimized_val}"
            
            # Output must be identical
            assert context_optimized.output_buffer == context_interpreted.output_buffer, \
                f"Output mismatch: interpreted={context_interpreted.output_buffer}, " \
                f"optimized={context_optimized.output_buffer}"
            
            # Optimized execution should be marked as such
            assert metrics.optimization_applied is True
            
        except Exception as e:
            pytest.fail(f"Optimized execution failed where interpreted succeeded: {e}")
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=20)
    def test_cache_consistency_semantic_equivalence(self, execution_count):
        """
        **Feature: aegis, Property 10f: Cache Consistency Semantic Equivalence**
        
        The optimized executor must produce identical results across multiple
        executions of the same code, whether cached or not, maintaining
        semantic equivalence with fresh interpreter executions.
        
        **Validates: Requirements 8.4**
        """
        # Create a simple program with unique hash for this test
        ast = [
            AssignmentNode("x", IntegerNode(42)),
            AssignmentNode("y", BinaryOpNode(IdentifierNode("x"), "+", IntegerNode(8))),
            PrintNode("y")
        ]
        
        code_hash = f"cache_consistency_test_{id(self)}_{execution_count}"  # Unique per test
        
        # Execute multiple times with optimized executor
        results = []
        for i in range(execution_count):
            context = ExecutionContext()
            metrics = self.optimizer.execute_optimized(code_hash, ast, context)
            
            result = {
                'variables': dict(context.variables),
                'output': list(context.output_buffer),
                'cache_hit': metrics.cache_hit
            }
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for i, result in enumerate(results[1:], 1):
            assert result['variables'] == first_result['variables'], \
                f"Execution {i}: variables differ from first execution"
            assert result['output'] == first_result['output'], \
                f"Execution {i}: output differs from first execution"
        
        # First execution should not be a cache hit, subsequent ones should be
        assert results[0]['cache_hit'] is False, "First execution should not be cache hit"
        if execution_count > 1:
            for i in range(1, execution_count):
                assert results[i]['cache_hit'] is True, f"Execution {i} should be cache hit"
        
        # Compare with fresh interpreter execution
        context_interpreted = ExecutionContext()
        self.interpreter.execute(ast, context_interpreted)
        
        assert first_result['variables'] == dict(context_interpreted.variables), \
            "Optimized results differ from interpreter"
        assert first_result['output'] == context_interpreted.output_buffer, \
            "Optimized output differs from interpreter"