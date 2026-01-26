"""
Property-based tests for AEGIS error message quality and descriptiveness.

These tests validate that error messages across all components provide
comprehensive, helpful, and consistent information for debugging and
user guidance.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from aegis.pipeline import AegisExecutionPipeline
from aegis.lexer import Lexer, LexerError
from aegis.parser import Parser, ParseError
from aegis.interpreter import StaticAnalyzer, AnalysisError, SandboxedInterpreter, InterpreterError
from aegis.interpreter.context import ExecutionContext
from aegis.runtime.monitor import RuntimeMonitor
from aegis.errors import (
    LexicalError, SyntaxError as AegisSyntaxError, SemanticError, 
    RuntimeError as AegisRuntimeError, SecurityError, AegisError
)
import tempfile
import os
import re


# Test data generators
@st.composite
def invalid_characters(draw):
    """Generate invalid characters for lexical errors."""
    # Characters that are not valid in AEGIS
    invalid_chars = ['@', '#', '$', '%', '^', '&', '!', '?', '~', '`', '[', ']', '{', '}', '|', '\\', '"', "'"]
    return draw(st.sampled_from(invalid_chars))


@st.composite
def invalid_syntax_programs(draw):
    """Generate programs with syntax errors."""
    programs = [
        "x = ",  # Missing operand
        "= 5",   # Missing variable
        "x + = 5",  # Invalid operator sequence
        "print",  # Missing argument
        "x = 5 +",  # Incomplete expression
        "x = (5",  # Unmatched parenthesis (if we add them later)
    ]
    return draw(st.sampled_from(programs))


@st.composite
def undefined_variable_programs(draw):
    """Generate programs with undefined variables."""
    var_names = draw(st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=8),
        min_size=1, max_size=3, unique=True
    ))
    
    # Use one undefined variable
    undefined_var = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=8))
    assume(undefined_var not in var_names)
    
    # Create program with defined variables and one undefined
    statements = []
    for var in var_names:
        value = draw(st.integers(min_value=1, max_value=100))
        statements.append(f"{var} = {value}")
    
    # Add statement using undefined variable
    statements.append(f"print {undefined_var}")
    
    return '\n'.join(statements)


class TestErrorMessageProperties:
    """Property-based tests for error message quality."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary trust file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.trust_file = self.temp_file.name
        
        # Initialize components
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
        self.pipeline = AegisExecutionPipeline(trust_file=self.trust_file)
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.trust_file):
            os.unlink(self.trust_file)
    
    @given(invalid_characters())
    @settings(max_examples=10, deadline=3000)
    def test_property_13_lexical_error_descriptiveness(self, invalid_char):
        """
        **Feature: aegis, Property 13: Error Message Descriptiveness (Lexical)**
        
        Validates that lexical error messages provide comprehensive information:
        - Clear identification of the problem
        - Precise location information (line, column)
        - Specific character or token causing the issue
        - Actionable suggestions for resolution
        - Consistent formatting and categorization
        """
        # Create source with invalid character
        source = f"x = 5 {invalid_char} 3"
        
        try:
            self.lexer.tokenize(source)
            pytest.fail("Expected LexerError but none was raised")
        except LexerError as e:
            # Test error message quality
            error_msg = str(e)
            
            # Should contain error category
            assert "[LEXICAL]" in error_msg, "Error should be categorized as LEXICAL"
            
            # Should contain error code
            assert "[LEX001]" in error_msg, "Error should have error code"
            
            # Should mention the invalid character
            assert invalid_char in error_msg, f"Error should mention invalid character '{invalid_char}'"
            
            # Should have location information
            assert hasattr(e, 'line'), "Error should have line information"
            assert hasattr(e, 'column'), "Error should have column information"
            assert e.line == 1, "Error should be on line 1"
            assert e.column > 0, "Error should have valid column number"
            
            # Should have suggestions
            assert "Suggestions:" in error_msg, "Error should provide suggestions"
            
            # Should be descriptive (not just a code or single word)
            assert len(error_msg) > 20, "Error message should be descriptive"
            
            # Should not contain internal implementation details
            assert "Exception" not in error_msg, "Error should not expose internal exception details"
            assert "Traceback" not in error_msg, "Error should not contain traceback"
    
    @given(invalid_syntax_programs())
    @settings(max_examples=10, deadline=3000)
    def test_property_13_syntax_error_descriptiveness(self, invalid_program):
        """
        **Feature: aegis, Property 13: Error Message Descriptiveness (Syntax)**
        
        Validates that syntax error messages provide comprehensive information:
        - Clear identification of syntax problem
        - Location information where parsing failed
        - Expected vs actual token information
        - Helpful suggestions for fixing syntax
        - Consistent error formatting
        """
        try:
            tokens = self.lexer.tokenize(invalid_program)
            self.parser.parse(tokens)
            pytest.fail("Expected ParseError but none was raised")
        except (LexerError, ParseError) as e:
            if isinstance(e, ParseError):
                error_msg = str(e)
                
                # Should contain error category
                assert "[SYNTAX]" in error_msg, "Error should be categorized as SYNTAX"
                
                # Should contain error code
                assert "[SYN001]" in error_msg, "Error should have error code"
                
                # Should have location information
                assert hasattr(e, 'line'), "Error should have line information"
                assert hasattr(e, 'column'), "Error should have column information"
                
                # Should have token information for compatibility
                assert hasattr(e, 'token'), "Error should have token information"
                
                # Should have suggestions
                assert "Suggestions:" in error_msg, "Error should provide suggestions"
                
                # Should be descriptive
                assert len(error_msg) > 15, "Error message should be descriptive"
                
                # Should mention what was expected or what went wrong
                assert any(word in error_msg.lower() for word in ['expected', 'unexpected', 'missing']), \
                    "Error should describe what was expected or what went wrong"
    
    @given(undefined_variable_programs())
    @settings(max_examples=10, deadline=5000)
    def test_property_13_semantic_error_descriptiveness(self, program_with_undefined_var):
        """
        **Feature: aegis, Property 13: Error Message Descriptiveness (Semantic)**
        
        Validates that semantic error messages provide comprehensive information:
        - Clear identification of semantic problem
        - Variable or construct causing the issue
        - Context about available alternatives
        - Actionable suggestions for resolution
        - Helpful guidance for common mistakes
        """
        result = self.pipeline.execute(program_with_undefined_var, verbose=False)
        
        # Should fail due to undefined variable
        assert not result.success, "Program with undefined variable should fail"
        assert result.error_message is not None, "Should have error message"
        
        error_msg = result.error_message
        
        # Should contain error category
        assert "[SEMANTIC]" in error_msg, "Error should be categorized as SEMANTIC"
        
        # Should contain error code
        assert "[SEM001]" in error_msg, "Error should have error code"
        
        # Should mention undefined variable
        assert "undefined" in error_msg.lower(), "Error should mention undefined variable"
        
        # Should have suggestions
        assert "Suggestions:" in error_msg, "Error should provide suggestions"
        
        # Should be descriptive and helpful
        assert len(error_msg) > 20, "Error message should be descriptive"
        
        # Should provide actionable advice
        assert any(word in error_msg.lower() for word in ['define', 'check', 'typo']), \
            "Error should provide actionable advice"
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=5, deadline=5000)
    def test_property_13_runtime_error_descriptiveness(self, divisor_base):
        """
        **Feature: aegis, Property 13: Error Message Descriptiveness (Runtime)**
        
        Validates that runtime error messages provide comprehensive information:
        - Clear identification of runtime problem
        - Current execution state information
        - Variable values and context
        - Specific suggestions for resolution
        - Execution context details
        """
        # Create program that will cause runtime division by zero
        program = f"""
x = {divisor_base * 10}
y = 0
result = x / y
print result
"""
        
        result = self.pipeline.execute(program, verbose=False)
        
        # Should fail due to division by zero
        assert not result.success, "Division by zero should fail"
        assert result.error_message is not None, "Should have error message"
        
        error_msg = result.error_message
        
        # Should contain error category
        assert "[RUNTIME]" in error_msg, "Error should be categorized as RUNTIME"
        
        # Should contain error code
        assert "[RUN001]" in error_msg, "Error should have error code"
        
        # Should mention division by zero
        assert "division by zero" in error_msg.lower(), "Error should mention division by zero"
        
        # Should show variable state
        assert "Variables:" in error_msg, "Error should show variable state"
        assert f"x={divisor_base * 10}" in error_msg, "Error should show variable x value"
        assert "y=0" in error_msg, "Error should show variable y value"
        
        # Should have suggestions
        assert "Suggestions:" in error_msg, "Error should provide suggestions"
        
        # Should be comprehensive
        assert len(error_msg) > 50, "Runtime error message should be comprehensive"
        
        # Should provide specific guidance
        assert "divisor" in error_msg.lower(), "Error should mention divisor"
    
    def test_property_13_error_consistency_across_components(self):
        """
        **Feature: aegis, Property 13: Error Message Descriptiveness (Consistency)**
        
        Validates that error messages are consistent across all components:
        - All errors follow the same formatting pattern
        - All errors include categorization and error codes
        - All errors provide suggestions when appropriate
        - Error severity is appropriately indicated
        - Context information is consistently formatted
        """
        test_cases = [
            # Lexical error
            ("x = @", "lexical"),
            # Syntax error  
            ("x = ", "syntax"),
            # Semantic error
            ("print undefined", "semantic"),
            # Runtime error (division by zero)
            ("x = 5\ny = 0\nz = x / y", "runtime")
        ]
        
        for program, expected_category in test_cases:
            result = self.pipeline.execute(program, verbose=False)
            
            if not result.success and result.error_message:
                error_msg = result.error_message
                
                # All errors should have category in brackets
                assert re.search(r'\[([A-Z]+)\]', error_msg), \
                    f"Error should have category in brackets: {error_msg}"
                
                # All errors should have error code
                assert re.search(r'\[[A-Z]{3}\d{3}\]', error_msg), \
                    f"Error should have error code: {error_msg}"
                
                # All errors should be multi-line and descriptive
                lines = error_msg.split('\n')
                assert len(lines) >= 2, f"Error should be multi-line: {error_msg}"
                
                # Should not contain raw exception text
                assert "Exception" not in error_msg, \
                    f"Error should not contain raw exception text: {error_msg}"
    
    def test_property_13_error_message_localization_readiness(self):
        """
        **Feature: aegis, Property 13: Error Message Descriptiveness (Localization)**
        
        Validates that error messages are structured for potential localization:
        - Error codes are consistent and unique
        - Message structure is predictable
        - Context information is separated from message text
        - Suggestions are clearly delineated
        """
        # Test various error types
        error_programs = [
            "x = @",  # Lexical
            "x = ",   # Syntax
            "print undefined",  # Semantic
        ]
        
        error_codes_seen = set()
        
        for program in error_programs:
            result = self.pipeline.execute(program, verbose=False)
            
            if not result.success and result.error_message:
                error_msg = result.error_message
                
                # Extract error code
                code_match = re.search(r'\[([A-Z]{3}\d{3})\]', error_msg)
                assert code_match, f"Should have error code: {error_msg}"
                
                error_code = code_match.group(1)
                assert error_code not in error_codes_seen, \
                    f"Error code {error_code} should be unique"
                error_codes_seen.add(error_code)
                
                # Should have structured suggestions
                if "Suggestions:" in error_msg:
                    suggestions_part = error_msg.split("Suggestions:")[1]
                    suggestion_lines = [line.strip() for line in suggestions_part.split('\n') if line.strip()]
                    
                    # Each suggestion should start with a dash
                    for suggestion in suggestion_lines:
                        if suggestion and not suggestion.startswith('-'):
                            continue  # Skip non-suggestion lines
                        assert suggestion.startswith('- '), \
                            f"Suggestions should start with '- ': {suggestion}"


if __name__ == "__main__":
    # Run a quick test
    test_instance = TestErrorMessageProperties()
    test_instance.setup_method()
    
    try:
        # Test lexical error
        test_instance.test_property_13_lexical_error_descriptiveness('@')
        print("✓ Lexical error test passed")
        
        # Test syntax error
        test_instance.test_property_13_syntax_error_descriptiveness("x = ")
        print("✓ Syntax error test passed")
        
        # Test semantic error
        test_instance.test_property_13_semantic_error_descriptiveness("x = 5\nprint undefined")
        print("✓ Semantic error test passed")
        
        # Test runtime error
        test_instance.test_property_13_runtime_error_descriptiveness(5)
        print("✓ Runtime error test passed")
        
        # Test consistency
        test_instance.test_property_13_error_consistency_across_components()
        print("✓ Error consistency test passed")
        
        print("\nAll error message quality tests passed!")
        
    finally:
        test_instance.teardown_method()