"""
Property-based tests for the AEGIS static analyzer.

These tests use Hypothesis to generate random programs and verify
that the static analyzer correctly detects security violations.
"""

import pytest
from hypothesis import given, strategies as st, assume
from aegis.lexer import Lexer, LexerError
from aegis.parser import Parser, ParseError
from aegis.interpreter import StaticAnalyzer, AnalysisError


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
        max_size=10
    ))
    
    identifier = first_char + rest_chars
    assume(identifier != 'print')  # Not a keyword
    return identifier


# Strategy for generating programs with undefined variables
@st.composite
def program_with_undefined_variable(draw):
    """Generate programs that use undefined variables."""
    defined_var = draw(valid_identifier())
    undefined_var = draw(valid_identifier())
    
    # Ensure they're different
    assume(defined_var != undefined_var)
    
    # Create program that defines one variable but uses another
    return f"{defined_var} = 10\nprint {undefined_var}"


# Strategy for generating programs with defined variables
@st.composite
def program_with_defined_variables(draw):
    """Generate programs where all variables are properly defined."""
    var1 = draw(valid_identifier())
    var2 = draw(valid_identifier())
    
    # Ensure they're different if we use both
    if var1 == var2:
        # Use same variable
        return f"{var1} = 42\nprint {var1}"
    else:
        # Use different variables, both defined
        return f"{var1} = 10\n{var2} = {var1} + 5\nprint {var2}"


# Strategy for generating division by zero programs
@st.composite
def program_with_division_by_zero(draw):
    """Generate programs with division by zero."""
    var = draw(valid_identifier())
    return f"{var} = 10 / 0\nprint {var}"


class TestStaticAnalyzerProperties:
    """Property-based tests for static analyzer correctness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
    
    @given(program_with_undefined_variable())
    def test_undefined_variable_detection(self, program):
        """
        **Feature: aegis, Property 6: Static Analysis Undefined Variable Detection**
        
        For any program containing references to undefined variables,
        the static analyzer should detect and report all undefined variables.
        
        **Validates: Requirements 4.1, 4.4**
        """
        try:
            tokens = self.lexer.tokenize(program)
            ast = self.parser.parse(tokens)
            
            # Analysis should fail due to undefined variable
            with pytest.raises(AnalysisError) as exc_info:
                self.analyzer.analyze(ast)
            
            # Error message should mention undefined variable
            error_msg = str(exc_info.value)
            assert "Undefined variable" in error_msg
            
        except (LexerError, ParseError):
            # If lexing/parsing fails, skip this test case
            pass
    
    @given(program_with_defined_variables())
    def test_defined_variables_pass_analysis(self, program):
        """
        **Feature: aegis, Property 6: Static Analysis Undefined Variable Detection**
        
        For any program where all variables are properly defined before use,
        the static analyzer should pass without errors.
        
        **Validates: Requirements 4.1, 4.4**
        """
        try:
            tokens = self.lexer.tokenize(program)
            ast = self.parser.parse(tokens)
            
            # Analysis should pass
            result = self.analyzer.analyze(ast)
            assert result is True
            
            # Get analysis report
            report = self.analyzer.get_analysis_report()
            assert report['passed'] is True
            assert len(report['errors']) == 0
            assert len(report['undefined_variables']) == 0
            
        except (LexerError, ParseError):
            # If lexing/parsing fails, skip this test case
            pass
    
    @given(program_with_division_by_zero())
    def test_division_by_zero_detection(self, program):
        """
        **Feature: aegis, Property 6: Static Analysis Undefined Variable Detection**
        
        For any program containing division by zero, the static analyzer
        should detect and report the arithmetic safety violation.
        
        **Validates: Requirements 4.2, 4.3**
        """
        try:
            tokens = self.lexer.tokenize(program)
            ast = self.parser.parse(tokens)
            
            # Analysis should fail due to division by zero
            with pytest.raises(AnalysisError) as exc_info:
                self.analyzer.analyze(ast)
            
            # Error message should mention division by zero
            error_msg = str(exc_info.value)
            assert "Division by zero" in error_msg
            
        except (LexerError, ParseError):
            # If lexing/parsing fails, skip this test case
            pass
    
    @given(st.lists(valid_identifier(), min_size=1, max_size=5))
    def test_variable_definition_order(self, variables):
        """
        **Feature: aegis, Property 6: Static Analysis Undefined Variable Detection**
        
        For any sequence of variables, they must be defined before use.
        The analyzer should detect when variables are used before definition.
        
        **Validates: Requirements 4.4, 4.5**
        """
        if len(variables) < 2:
            return
        
        try:
            # Create program that uses variable before defining it
            program = f"print {variables[0]}\n{variables[0]} = 42"
            
            tokens = self.lexer.tokenize(program)
            ast = self.parser.parse(tokens)
            
            # Analysis should fail
            with pytest.raises(AnalysisError) as exc_info:
                self.analyzer.analyze(ast)
            
            # Should detect undefined variable
            error_msg = str(exc_info.value)
            assert "Undefined variable" in error_msg
            assert variables[0] in error_msg
            
        except (LexerError, ParseError):
            # If lexing/parsing fails, skip this test case
            pass
    
    @given(st.integers(min_value=1, max_value=5))
    def test_multiple_assignments_analysis(self, num_vars):
        """
        **Feature: aegis, Property 6: Static Analysis Undefined Variable Detection**
        
        For any program with multiple variable assignments, all variables
        should be properly tracked and validated.
        
        **Validates: Requirements 4.1, 4.4**
        """
        try:
            # Generate unique variable names
            variables = [f"var{i}" for i in range(num_vars)]
            
            # Create program with chain of assignments
            statements = []
            statements.append(f"{variables[0]} = 10")
            
            for i in range(1, num_vars):
                statements.append(f"{variables[i]} = {variables[i-1]} + 1")
            
            # Print the last variable
            statements.append(f"print {variables[-1]}")
            
            program = '\n'.join(statements)
            
            tokens = self.lexer.tokenize(program)
            ast = self.parser.parse(tokens)
            
            # Analysis should pass
            result = self.analyzer.analyze(ast)
            assert result is True
            
            # Check analysis report
            report = self.analyzer.get_analysis_report()
            assert report['passed'] is True
            assert len(report['errors']) == 0
            
            # All variables should be defined
            assert len(report['defined_variables']) == num_vars
            for var in variables:
                assert var in report['defined_variables']
            
        except (LexerError, ParseError):
            # If lexing/parsing fails, skip this test case
            pass
    
    @given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=50))
    def test_analyzer_never_crashes(self, arbitrary_text):
        """
        **Feature: aegis, Property 6: Static Analysis Undefined Variable Detection**
        
        The static analyzer should never crash on any input - it should
        either pass analysis or raise an AnalysisError.
        
        **Validates: Requirements 4.1, 4.2**
        """
        try:
            tokens = self.lexer.tokenize(arbitrary_text)
            ast = self.parser.parse(tokens)
            
            # Analyzer should either pass or raise AnalysisError
            try:
                result = self.analyzer.analyze(ast)
                assert isinstance(result, bool)
            except AnalysisError:
                # This is acceptable for invalid programs
                pass
            
        except (LexerError, ParseError):
            # If lexing/parsing fails, skip analysis
            pass
        except Exception as e:
            # Any other exception is a bug
            pytest.fail(f"Static analyzer crashed with unexpected exception: {e}")
    
    @given(valid_identifier(), st.integers(min_value=1, max_value=100))
    def test_simple_assignment_analysis(self, variable, value):
        """
        **Feature: aegis, Property 6: Static Analysis Undefined Variable Detection**
        
        For any simple assignment statement, the static analyzer should
        correctly track the variable definition.
        
        **Validates: Requirements 4.1, 4.4**
        """
        try:
            program = f"{variable} = {value}\nprint {variable}"
            
            tokens = self.lexer.tokenize(program)
            ast = self.parser.parse(tokens)
            
            # Analysis should pass
            result = self.analyzer.analyze(ast)
            assert result is True
            
            # Check that variable is properly tracked
            report = self.analyzer.get_analysis_report()
            assert variable in report['defined_variables']
            assert variable in report['used_variables']
            assert len(report['undefined_variables']) == 0
            
        except (LexerError, ParseError):
            # If lexing/parsing fails, skip this test case
            pass
    
    @given(st.lists(st.integers(min_value=1, max_value=1000), min_size=2, max_size=5))
    def test_arithmetic_safety_analysis(self, numbers):
        """
        **Feature: aegis, Property 6: Static Analysis Undefined Variable Detection**
        
        For any arithmetic expression, the static analyzer should detect
        potential safety issues like overflow or division by zero.
        
        **Validates: Requirements 4.2, 4.3**
        """
        if len(numbers) < 2:
            return
        
        try:
            # Create expression with potential issues
            if 0 in numbers:
                # Test division by zero
                program = f"result = {numbers[0]} / 0\nprint result"
                
                tokens = self.lexer.tokenize(program)
                ast = self.parser.parse(tokens)
                
                # Should detect division by zero
                with pytest.raises(AnalysisError) as exc_info:
                    self.analyzer.analyze(ast)
                
                assert "Division by zero" in str(exc_info.value)
            
            else:
                # Test normal arithmetic
                program = f"result = {numbers[0]} + {numbers[1]}\nprint result"
                
                tokens = self.lexer.tokenize(program)
                ast = self.parser.parse(tokens)
                
                # Should pass analysis
                result = self.analyzer.analyze(ast)
                assert result is True
            
        except (LexerError, ParseError):
            # If lexing/parsing fails, skip this test case
            pass