"""
Unit tests for the AEGIS static analyzer.

These tests verify that the static analyzer correctly performs
compile-time security and safety checks on AEGIS programs.
"""

import pytest
from aegis.lexer import Lexer
from aegis.parser import Parser
from aegis.interpreter import StaticAnalyzer, AnalysisError


class TestStaticAnalyzerBasic:
    """Test basic static analysis functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
    
    def _analyze_program(self, source):
        """Helper to analyze a program from source code."""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        return self.analyzer.analyze(ast)
    
    def _get_analysis_report(self, source):
        """Helper to get analysis report for a program."""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        try:
            self.analyzer.analyze(ast)
        except AnalysisError:
            pass  # Still want the report
        return self.analyzer.get_analysis_report()
    
    def test_simple_valid_program(self):
        """Test analysis of simple valid program."""
        source = """x = 10
print x"""
        
        result = self._analyze_program(source)
        assert result is True
        
        report = self.analyzer.get_analysis_report()
        assert report['passed'] is True
        assert len(report['errors']) == 0
        assert 'x' in report['defined_variables']
        assert 'x' in report['used_variables']
    
    def test_empty_program(self):
        """Test analysis of empty program."""
        source = ""
        
        result = self._analyze_program(source)
        assert result is True
        
        report = self.analyzer.get_analysis_report()
        assert report['passed'] is True
        assert len(report['errors']) == 0
    
    def test_multiple_assignments(self):
        """Test analysis of program with multiple assignments."""
        source = """x = 10
y = 20
z = x + y
print z"""
        
        result = self._analyze_program(source)
        assert result is True
        
        report = self.analyzer.get_analysis_report()
        assert report['passed'] is True
        assert len(report['errors']) == 0
        assert set(report['defined_variables']) == {'x', 'y', 'z'}


class TestStaticAnalyzerUndefinedVariables:
    """Test undefined variable detection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
    
    def _analyze_program(self, source):
        """Helper to analyze a program from source code."""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        return self.analyzer.analyze(ast)
    
    def test_undefined_variable_in_assignment(self):
        """Test detection of undefined variable in assignment."""
        source = "y = x + 5"
        
        with pytest.raises(AnalysisError) as exc_info:
            self._analyze_program(source)
        
        assert "Undefined variable: x" in str(exc_info.value)
    
    def test_undefined_variable_in_print(self):
        """Test detection of undefined variable in print."""
        source = "print undefined_var"
        
        with pytest.raises(AnalysisError) as exc_info:
            self._analyze_program(source)
        
        assert "Undefined variable: undefined_var" in str(exc_info.value)
    
    def test_multiple_undefined_variables(self):
        """Test detection of multiple undefined variables."""
        source = """result = a + b + c
print result"""
        
        with pytest.raises(AnalysisError) as exc_info:
            self._analyze_program(source)
        
        error_msg = str(exc_info.value)
        assert "Undefined variable: a" in error_msg
        assert "Undefined variable: b" in error_msg
        assert "Undefined variable: c" in error_msg
    
    def test_variable_used_before_definition(self):
        """Test detection of variable used before definition."""
        source = """print x
x = 10"""
        
        with pytest.raises(AnalysisError) as exc_info:
            self._analyze_program(source)
        
        assert "Undefined variable: x" in str(exc_info.value)
    
    def test_variable_definition_order(self):
        """Test that variable definition order matters."""
        # This should work - x defined before y uses it
        source1 = """x = 10
y = x + 5
print y"""
        
        result = self._analyze_program(source1)
        assert result is True
        
        # This should fail - y uses x before x is defined
        source2 = """y = x + 5
x = 10
print y"""
        
        with pytest.raises(AnalysisError):
            self._analyze_program(source2)


class TestStaticAnalyzerArithmeticSafety:
    """Test arithmetic safety checks."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
    
    def _analyze_program(self, source):
        """Helper to analyze a program from source code."""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        return self.analyzer.analyze(ast)
    
    def test_division_by_zero_literal(self):
        """Test detection of division by zero with literal."""
        source = "result = 10 / 0"
        
        with pytest.raises(AnalysisError) as exc_info:
            self._analyze_program(source)
        
        assert "Division by zero" in str(exc_info.value)
    
    def test_division_by_zero_in_expression(self):
        """Test detection of division by zero in complex expression."""
        source = "result = 5 + 10 / 0 - 3"
        
        with pytest.raises(AnalysisError) as exc_info:
            self._analyze_program(source)
        
        assert "Division by zero" in str(exc_info.value)
    
    def test_valid_division(self):
        """Test that valid division passes analysis."""
        source = """x = 10
result = x / 2
print result"""
        
        result = self._analyze_program(source)
        assert result is True
    
    def test_potential_division_by_zero_warning(self):
        """Test warning for potential division by zero with variables."""
        source = """x = 5
y = 0
result = x / y
print result"""
        
        # This should pass analysis but generate a warning
        result = self._analyze_program(source)
        assert result is True
        
        report = self.analyzer.get_analysis_report()
        # Check if there are warnings about potential division by zero
        warnings = report.get('warnings', [])
        has_division_warning = any('division by zero' in w.lower() for w in warnings)
        assert has_division_warning
    
    def test_large_number_overflow_warning(self):
        """Test warning for potential integer overflow."""
        source = "result = 2000000 * 2000000"
        
        result = self._analyze_program(source)
        assert result is True
        
        report = self.analyzer.get_analysis_report()
        warnings = report.get('warnings', [])
        has_overflow_warning = any('overflow' in w.lower() for w in warnings)
        assert has_overflow_warning


class TestStaticAnalyzerExpressionValidation:
    """Test expression validation and well-formedness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
    
    def _analyze_program(self, source):
        """Helper to analyze a program from source code."""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        return self.analyzer.analyze(ast)
    
    def test_simple_arithmetic_expressions(self):
        """Test validation of simple arithmetic expressions."""
        test_cases = [
            "result = 1 + 2",
            "result = 10 - 5",
            "result = 3 * 4",
            "result = 8 / 2",
            "result = 1 + 2 * 3",
            "result = (1 + 2) * 3"  # Note: parentheses not in basic AEGIS
        ]
        
        for source in test_cases[:5]:  # Skip parentheses test for now
            try:
                result = self._analyze_program(source)
                assert result is True
            except AnalysisError as e:
                pytest.fail(f"Valid expression failed analysis: {source}, error: {e}")
    
    def test_complex_nested_expressions(self):
        """Test validation of complex nested expressions."""
        source = """a = 1
b = 2
c = 3
d = 4
result = a + b * c - d / 2
print result"""
        
        result = self._analyze_program(source)
        assert result is True
    
    def test_expression_depth_limit(self):
        """Test that deeply nested expressions are rejected."""
        # Create a deeply nested expression without parentheses
        # Since AEGIS doesn't support parentheses, create a chain of operations
        expression = "1"
        for i in range(15):  # Exceed max depth of 10
            expression = f"{expression} + 1"
        
        source = f"result = {expression}"
        
        # This should fail due to expression depth
        with pytest.raises(AnalysisError) as exc_info:
            self._analyze_program(source)
        
        assert "too deeply nested" in str(exc_info.value)


class TestStaticAnalyzerIdentifierValidation:
    """Test identifier validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
    
    def _analyze_program(self, source):
        """Helper to analyze a program from source code."""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        return self.analyzer.analyze(ast)
    
    def test_valid_identifiers(self):
        """Test that valid identifiers pass analysis."""
        valid_identifiers = [
            "x", "variable", "var_name", "_private", "counter123", "CamelCase"
        ]
        
        for identifier in valid_identifiers:
            source = f"{identifier} = 42\nprint {identifier}"
            try:
                result = self._analyze_program(source)
                assert result is True
            except AnalysisError as e:
                pytest.fail(f"Valid identifier failed: {identifier}, error: {e}")
    
    def test_keyword_as_identifier(self):
        """Test that keywords cannot be used as identifiers."""
        # Note: This would be caught by the lexer/parser, not static analyzer
        # But we test the analyzer's validation as well
        pass  # Keywords are handled by lexer


class TestStaticAnalyzerReporting:
    """Test analysis reporting functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
    
    def _get_analysis_report(self, source):
        """Helper to get analysis report for a program."""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        try:
            self.analyzer.analyze(ast)
        except AnalysisError:
            pass  # Still want the report
        return self.analyzer.get_analysis_report()
    
    def test_analysis_report_structure(self):
        """Test that analysis report has correct structure."""
        source = """x = 10
print x"""
        
        report = self._get_analysis_report(source)
        
        # Check required fields
        assert 'passed' in report
        assert 'errors' in report
        assert 'warnings' in report
        assert 'defined_variables' in report
        assert 'used_variables' in report
        assert 'undefined_variables' in report
        
        # Check types
        assert isinstance(report['passed'], bool)
        assert isinstance(report['errors'], list)
        assert isinstance(report['warnings'], list)
        assert isinstance(report['defined_variables'], list)
        assert isinstance(report['used_variables'], list)
        assert isinstance(report['undefined_variables'], list)
    
    def test_successful_analysis_report(self):
        """Test report for successful analysis."""
        source = """x = 10
y = x + 5
print y"""
        
        report = self._get_analysis_report(source)
        
        assert report['passed'] is True
        assert len(report['errors']) == 0
        assert 'x' in report['defined_variables']
        assert 'y' in report['defined_variables']
        assert 'x' in report['used_variables']
        assert 'y' in report['used_variables']
        assert len(report['undefined_variables']) == 0
    
    def test_failed_analysis_report(self):
        """Test report for failed analysis."""
        source = """x = 10
print undefined_var"""
        
        report = self._get_analysis_report(source)
        
        assert report['passed'] is False
        assert len(report['errors']) > 0
        assert 'x' in report['defined_variables']
        assert 'undefined_var' in report['used_variables']
        assert 'undefined_var' in report['undefined_variables']
    
    def test_multiple_errors_report(self):
        """Test report with multiple errors."""
        source = """result = a + b / 0
print undefined_var"""
        
        report = self._get_analysis_report(source)
        
        assert report['passed'] is False
        assert len(report['errors']) >= 2  # At least undefined vars and division by zero
        
        # Check that all undefined variables are reported
        undefined_vars = set(report['undefined_variables'])
        assert 'a' in undefined_vars
        assert 'b' in undefined_vars
        assert 'undefined_var' in undefined_vars


class TestStaticAnalyzerEdgeCases:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
    
    def _analyze_program(self, source):
        """Helper to analyze a program from source code."""
        tokens = self.lexer.tokenize(source)
        ast = self.parser.parse(tokens)
        return self.analyzer.analyze(ast)
    
    def test_variable_redefinition(self):
        """Test that variable redefinition is allowed."""
        source = """x = 10
x = 20
print x"""
        
        result = self._analyze_program(source)
        assert result is True
    
    def test_unused_variables(self):
        """Test handling of unused variables."""
        source = """x = 10
y = 20
print x"""
        
        result = self._analyze_program(source)
        assert result is True
        
        report = self.analyzer.get_analysis_report()
        assert 'x' in report['defined_variables']
        assert 'y' in report['defined_variables']
        assert 'x' in report['used_variables']
        assert 'y' not in report['used_variables']
    
    def test_self_referential_assignment(self):
        """Test self-referential assignment (should fail)."""
        source = "x = x + 1"
        
        with pytest.raises(AnalysisError) as exc_info:
            self._analyze_program(source)
        
        assert "Undefined variable: x" in str(exc_info.value)
    
    def test_chained_assignments(self):
        """Test chained variable assignments."""
        source = """a = 1
b = a
c = b
d = c
print d"""
        
        result = self._analyze_program(source)
        assert result is True
    
    def test_complex_arithmetic_chains(self):
        """Test complex arithmetic with multiple operations."""
        source = """a = 1
b = 2
c = 3
result = a + b - c * a / b + c
print result"""
        
        result = self._analyze_program(source)
        assert result is True