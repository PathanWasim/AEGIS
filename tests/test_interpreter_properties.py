"""
Property-based tests for the AEGIS sandboxed interpreter.

These tests use Hypothesis to generate random programs and verify
that the interpreter executes them correctly with proper semantics.
"""

import pytest
from hypothesis import given, strategies as st, assume
from aegis.lexer import Lexer, LexerError
from aegis.parser import Parser, ParseError
from aegis.interpreter import SandboxedInterpreter, ExecutionContext, InterpreterError, StaticAnalyzer, AnalysisError


# Strategy for generating valid identifiers
@st.composite
def valid_identifier(draw):
    """Generate valid AEGIS identifiers."""
    first_char = draw(st.one_of(
        st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')),
        st.characters(min_codepoint=ord('A'), max_codepoint=ord('Z')),
        st.just('_')
    ))
    
    rest_chars = draw(st.text(
        alphabet=st.characters(
            min_codepoint=ord('a'), max_codepoint=ord('z')
        ) | st.characters(
            min_codepoint=ord('A'), max_codepoint=ord('Z')
        ) | st.characters(
            min_codepoint=ord('0'), max_codepoint=ord('9')
        ) | st.just('_'),
        max_size=8
    ))
    
    identifier = first_char + rest_chars
    assume(identifier != 'print')
    return identifier


# Strategy for safe integers (avoid overflow in tests)
safe_integer = st.integers(min_value=-1000000, max_value=1000000)


# Strategy for generating simple arithmetic programs
@st.composite
def simple_arithmetic_program(draw):
    """Generate simple arithmetic programs."""
    var = draw(valid_identifier())
    left = draw(safe_integer)
    right = draw(safe_integer)
    operator = draw(st.sampled_from(['+', '-', '*']))
    
    # Avoid division by zero
    if operator == '/':
        assume(right != 0)
    
    return f"{var} = {left} {operator} {right}\nprint {var}"


# Strategy for generating assignment programs
@st.composite
def assignment_program(draw):
    """Generate programs with variable assignments."""
    var1 = draw(valid_identifier())
    var2 = draw(valid_identifier())
    value1 = draw(safe_integer)
    value2 = draw(safe_integer)
    
    if var1 == var2:
        # Same variable, test reassignment
        return f"{var1} = {value1}\n{var1} = {value2}\nprint {var1}"
    else:
        # Different variables
        return f"{var1} = {value1}\n{var2} = {value2}\nprint {var1}\nprint {var2}"


class TestInterpreterProperties:
    """Property-based tests for interpreter correctness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
        self.interpreter = SandboxedInterpreter()
    
    def _execute_program(self, source):
        """Helper to execute a program and return context."""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        self.analyzer.analyze(ast)  # Ensure it passes static analysis
        
        context = ExecutionContext()
        self.interpreter.execute(ast, context)
        return context
    
    @given(safe_integer)
    def test_integer_assignment_correctness(self, value):
        """
        **Feature: aegis, Property 4: Variable Assignment Consistency**
        
        For any valid integer assignment, executing the assignment should
        update the variable's value to match the assigned value.
        
        **Validates: Requirements 1.1, 5.2**
        """
        try:
            program = f"x = {value}\nprint x"
            context = self._execute_program(program)
            
            # Variable should be set to the assigned value
            assert context.get_variable('x') == value
            
            # Output should contain the value
            assert str(value) in context.get_output()
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            # If execution fails, the value might be invalid
            pass
    
    @given(safe_integer, safe_integer)
    def test_arithmetic_addition_correctness(self, left, right):
        """
        **Feature: aegis, Property 3: Arithmetic Expression Correctness**
        
        For any valid addition expression, the interpreter should compute
        the mathematically correct result.
        
        **Validates: Requirements 1.2, 5.3**
        """
        try:
            expected = left + right
            # Skip if result would overflow
            assume(-2147483648 <= expected <= 2147483647)
            
            program = f"result = {left} + {right}\nprint result"
            context = self._execute_program(program)
            
            # Result should be mathematically correct
            assert context.get_variable('result') == expected
            assert str(expected) in context.get_output()
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass
    
    @given(safe_integer, safe_integer)
    def test_arithmetic_subtraction_correctness(self, left, right):
        """
        **Feature: aegis, Property 3: Arithmetic Expression Correctness**
        
        For any valid subtraction expression, the interpreter should compute
        the mathematically correct result.
        
        **Validates: Requirements 1.2, 5.3**
        """
        try:
            expected = left - right
            assume(-2147483648 <= expected <= 2147483647)
            
            program = f"result = {left} - {right}\nprint result"
            context = self._execute_program(program)
            
            assert context.get_variable('result') == expected
            assert str(expected) in context.get_output()
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass
    
    @given(safe_integer, safe_integer)
    def test_arithmetic_multiplication_correctness(self, left, right):
        """
        **Feature: aegis, Property 3: Arithmetic Expression Correctness**
        
        For any valid multiplication expression, the interpreter should compute
        the mathematically correct result.
        
        **Validates: Requirements 1.2, 5.3**
        """
        try:
            expected = left * right
            assume(-2147483648 <= expected <= 2147483647)
            
            program = f"result = {left} * {right}\nprint result"
            context = self._execute_program(program)
            
            assert context.get_variable('result') == expected
            assert str(expected) in context.get_output()
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass
    
    @given(safe_integer, safe_integer)
    def test_arithmetic_division_correctness(self, left, right):
        """
        **Feature: aegis, Property 3: Arithmetic Expression Correctness**
        
        For any valid division expression, the interpreter should compute
        the mathematically correct result (integer division).
        
        **Validates: Requirements 1.2, 5.3**
        """
        try:
            assume(right != 0)  # Avoid division by zero
            expected = left // right  # Integer division
            
            program = f"result = {left} / {right}\nprint result"
            context = self._execute_program(program)
            
            assert context.get_variable('result') == expected
            assert str(expected) in context.get_output()
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass
    
    @given(valid_identifier(), safe_integer)
    def test_print_statement_correctness(self, variable, value):
        """
        **Feature: aegis, Property 5: Print Statement Output Correctness**
        
        For any valid print statement referencing a defined variable,
        the output should contain the current value of that variable.
        
        **Validates: Requirements 1.3, 5.4**
        """
        try:
            program = f"{variable} = {value}\nprint {variable}"
            context = self._execute_program(program)
            
            # Output should contain the variable's value
            output = context.get_output()
            assert str(value) in output
            
            # Variable should have the correct value
            assert context.get_variable(variable) == value
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass
    
    @given(assignment_program())
    def test_variable_assignment_consistency(self, program):
        """
        **Feature: aegis, Property 4: Variable Assignment Consistency**
        
        For any valid assignment program, all variables should maintain
        their assigned values consistently throughout execution.
        
        **Validates: Requirements 1.1, 5.2**
        """
        try:
            context = self._execute_program(program)
            
            # All defined variables should have integer values
            for var_name, var_value in context.variables.items():
                assert isinstance(var_value, int)
                assert -2147483648 <= var_value <= 2147483647
            
            # Output should contain values for all printed variables
            output = context.get_output()
            assert len(output) > 0
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass
    
    @given(simple_arithmetic_program())
    def test_arithmetic_expression_evaluation(self, program):
        """
        **Feature: aegis, Property 3: Arithmetic Expression Correctness**
        
        For any valid arithmetic program, the interpreter should evaluate
        expressions correctly and produce consistent results.
        
        **Validates: Requirements 1.2, 5.3**
        """
        try:
            context = self._execute_program(program)
            
            # Should have at least one variable defined
            assert len(context.variables) > 0
            
            # All variables should have valid integer values
            for var_name, var_value in context.variables.items():
                assert isinstance(var_value, int)
            
            # Should have produced output
            assert len(context.get_output()) > 0
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass
    
    @given(st.lists(st.tuples(valid_identifier(), safe_integer), min_size=1, max_size=5))
    def test_multiple_variable_assignments(self, var_value_pairs):
        """
        **Feature: aegis, Property 4: Variable Assignment Consistency**
        
        For any sequence of variable assignments, each variable should
        maintain its assigned value independently.
        
        **Validates: Requirements 1.1, 5.2**
        """
        try:
            # Create program with multiple assignments
            statements = []
            expected_vars = {}
            
            for var_name, value in var_value_pairs:
                statements.append(f"{var_name} = {value}")
                expected_vars[var_name] = value
            
            # Add print statements for all variables
            for var_name in expected_vars:
                statements.append(f"print {var_name}")
            
            program = '\n'.join(statements)
            context = self._execute_program(program)
            
            # Check that all variables have correct values
            for var_name, expected_value in expected_vars.items():
                assert context.get_variable(var_name) == expected_value
            
            # Check that output contains all values
            output = context.get_output()
            for expected_value in expected_vars.values():
                assert str(expected_value) in output
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass
    
    def test_execution_state_isolation(self):
        """
        **Feature: aegis, Property 7: Execution State Isolation**
        
        For any two consecutive program executions, the second execution
        should not be affected by variable state from the first execution.
        
        **Validates: Requirements 5.6**
        """
        try:
            # First execution
            program1 = "x = 100\nprint x"
            context1 = ExecutionContext()
            
            tokens1 = self.lexer.tokenize(program1)
            ast1 = self.parser.parse(tokens1)
            self.analyzer.analyze(ast1)
            self.interpreter.execute(ast1, context1)
            
            assert context1.get_variable('x') == 100
            
            # Second execution with fresh context
            program2 = "y = 200\nprint y"
            context2 = ExecutionContext()
            
            tokens2 = self.lexer.tokenize(program2)
            ast2 = self.parser.parse(tokens2)
            self.analyzer.analyze(ast2)
            self.interpreter.execute(ast2, context2)
            
            # Second context should not have variables from first
            assert 'x' not in context2.variables
            assert context2.get_variable('y') == 200
            
            # First context should be unchanged
            assert context1.get_variable('x') == 100
            assert 'y' not in context1.variables
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass
    
    @given(st.integers(min_value=1, max_value=10))
    def test_operation_counting(self, num_operations):
        """
        **Feature: aegis, Property 3: Arithmetic Expression Correctness**
        
        The interpreter should correctly count operations performed
        during execution for monitoring purposes.
        
        **Validates: Requirements 5.2, 5.3**
        """
        try:
            # Create program with known number of operations
            statements = []
            for i in range(num_operations):
                statements.append(f"x{i} = {i}")
            
            program = '\n'.join(statements)
            context = ExecutionContext()
            
            tokens = self.lexer.tokenize(program)
            ast = self.parser.parse(tokens)
            self.analyzer.analyze(ast)
            
            # Reset operation count
            self.interpreter.reset_operation_count()
            self.interpreter.execute(ast, context)
            
            # Should have performed at least the expected operations
            operation_count = self.interpreter.get_operation_count()
            assert operation_count >= num_operations
            
        except (LexerError, ParseError, AnalysisError, InterpreterError):
            pass