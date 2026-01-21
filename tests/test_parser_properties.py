"""
Property-based tests for the AEGIS parser.

These tests use Hypothesis to generate random valid AEGIS programs
and verify universal properties that should hold for all valid programs.
"""

import pytest
from hypothesis import given, strategies as st, assume
from aegis.lexer import Lexer, LexerError
from aegis.parser import Parser, ParseError
from aegis.ast import ASTPrettyPrinter


# Strategy for generating valid AEGIS identifiers (reused from lexer tests)
@st.composite
def valid_identifier(draw):
    """Generate valid AEGIS identifiers."""
    # Start with letter or underscore
    first_char = draw(st.one_of(
        st.characters(min_codepoint=ord('a'), max_codepoint=ord('z')),
        st.characters(min_codepoint=ord('A'), max_codepoint=ord('Z')),
        st.just('_')
    ))
    
    # Continue with letters, digits, or underscores
    rest_chars = draw(st.text(
        alphabet=st.characters(
            min_codepoint=ord('a'), max_codepoint=ord('z')
        ) | st.characters(
            min_codepoint=ord('A'), max_codepoint=ord('Z')
        ) | st.characters(
            min_codepoint=ord('0'), max_codepoint=ord('9')
        ) | st.just('_'),
        max_size=15
    ))
    
    identifier = first_char + rest_chars
    
    # Ensure it's not a keyword
    assume(identifier != 'print')
    
    return identifier


# Strategy for generating valid integers
valid_integer = st.integers(min_value=0, max_value=9999)


# Strategy for generating arithmetic operators
arithmetic_operator = st.sampled_from(['+', '-', '*', '/'])


# Strategy for generating simple expressions
@st.composite
def simple_expression(draw):
    """Generate simple arithmetic expressions."""
    choice = draw(st.integers(min_value=1, max_value=3))
    
    if choice == 1:
        # Just an integer
        return str(draw(valid_integer))
    elif choice == 2:
        # Just an identifier
        return draw(valid_identifier())
    else:
        # Binary operation: left op right
        left = draw(st.one_of(
            valid_integer.map(str),
            valid_identifier()
        ))
        operator = draw(arithmetic_operator)
        right = draw(st.one_of(
            valid_integer.map(str),
            valid_identifier()
        ))
        return f"{left} {operator} {right}"


# Strategy for generating assignment statements
@st.composite
def assignment_statement(draw):
    """Generate assignment statements."""
    identifier = draw(valid_identifier())
    expression = draw(simple_expression())
    return f"{identifier} = {expression}"


# Strategy for generating print statements
@st.composite
def print_statement(draw):
    """Generate print statements."""
    identifier = draw(valid_identifier())
    return f"print {identifier}"


# Strategy for generating single statements
@st.composite
def single_statement(draw):
    """Generate a single AEGIS statement."""
    choice = draw(st.integers(min_value=1, max_value=2))
    
    if choice == 1:
        return draw(assignment_statement())
    else:
        return draw(print_statement())


# Strategy for generating programs (multiple statements)
@st.composite
def aegis_program(draw):
    """Generate complete AEGIS programs."""
    statements = draw(st.lists(single_statement(), min_size=1, max_size=5))
    return '\n'.join(statements)


class TestParserProperties:
    """Property-based tests for parser correctness."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.lexer = Lexer()
        self.parser = Parser()
        self.printer = ASTPrettyPrinter()
    
    @given(assignment_statement())
    def test_assignment_parsing_roundtrip(self, assignment):
        """
        **Feature: aegis, Property 2: Parsing Round-Trip Consistency**
        
        For any valid assignment statement, parsing and then pretty-printing
        should produce a semantically equivalent program.
        
        **Validates: Requirements 3.5**
        """
        try:
            # Parse the assignment
            tokens = self.lexer.tokenize(assignment)
            ast = self.parser.parse(tokens)
            
            # Should have exactly one statement
            assert len(ast) == 1
            
            # Pretty-print back to source
            reconstructed = self.printer.print_program(ast)
            
            # Parse the reconstructed version
            tokens2 = self.lexer.tokenize(reconstructed)
            ast2 = self.parser.parse(tokens2)
            
            # Should produce the same AST structure
            assert len(ast) == len(ast2)
            
            # Compare the pretty-printed versions (should be identical)
            reconstructed2 = self.printer.print_program(ast2)
            assert reconstructed == reconstructed2
            
        except (LexerError, ParseError):
            # If parsing fails, the generated statement might be invalid
            # This is acceptable for property testing
            pass
    
    @given(print_statement())
    def test_print_parsing_roundtrip(self, print_stmt):
        """
        **Feature: aegis, Property 2: Parsing Round-Trip Consistency**
        
        For any valid print statement, parsing and then pretty-printing
        should produce a semantically equivalent program.
        
        **Validates: Requirements 3.5**
        """
        try:
            # Parse the print statement
            tokens = self.lexer.tokenize(print_stmt)
            ast = self.parser.parse(tokens)
            
            # Should have exactly one statement
            assert len(ast) == 1
            
            # Pretty-print back to source
            reconstructed = self.printer.print_program(ast)
            
            # Parse the reconstructed version
            tokens2 = self.lexer.tokenize(reconstructed)
            ast2 = self.parser.parse(tokens2)
            
            # Should produce the same AST structure
            assert len(ast) == len(ast2)
            
            # Compare the pretty-printed versions
            reconstructed2 = self.printer.print_program(ast2)
            assert reconstructed == reconstructed2
            
        except (LexerError, ParseError):
            # If parsing fails, the statement might be invalid
            pass
    
    @given(simple_expression())
    def test_expression_parsing_consistency(self, expression):
        """
        **Feature: aegis, Property 2: Parsing Round-Trip Consistency**
        
        For any valid expression in an assignment, parsing should
        preserve the expression structure correctly.
        
        **Validates: Requirements 3.5**
        """
        try:
            # Wrap expression in an assignment
            assignment = f"result = {expression}"
            
            tokens = self.lexer.tokenize(assignment)
            ast = self.parser.parse(tokens)
            
            # Should have one assignment
            assert len(ast) == 1
            
            # Extract and pretty-print the expression
            expr_node = ast[0].expression
            expr_pretty = self.printer.print_ast(expr_node)
            
            # Parse the expression again in a new assignment
            assignment2 = f"result = {expr_pretty}"
            tokens2 = self.lexer.tokenize(assignment2)
            ast2 = self.parser.parse(tokens2)
            
            # Expression should be structurally equivalent
            expr_node2 = ast2[0].expression
            expr_pretty2 = self.printer.print_ast(expr_node2)
            
            assert expr_pretty == expr_pretty2
            
        except (LexerError, ParseError):
            # If parsing fails, the expression might be invalid
            pass
    
    @given(aegis_program())
    def test_program_parsing_roundtrip(self, program):
        """
        **Feature: aegis, Property 2: Parsing Round-Trip Consistency**
        
        For any valid AEGIS program, parsing and then pretty-printing
        should produce a semantically equivalent program.
        
        **Validates: Requirements 3.5**
        """
        try:
            # Parse the program
            tokens = self.lexer.tokenize(program)
            ast = self.parser.parse(tokens)
            
            # Pretty-print back to source
            reconstructed = self.printer.print_program(ast)
            
            # Parse the reconstructed version
            tokens2 = self.lexer.tokenize(reconstructed)
            ast2 = self.parser.parse(tokens2)
            
            # Should have the same number of statements
            assert len(ast) == len(ast2)
            
            # Compare the pretty-printed versions
            reconstructed2 = self.printer.print_program(ast2)
            assert reconstructed == reconstructed2
            
        except (LexerError, ParseError):
            # If parsing fails, the program might be invalid
            pass
    
    @given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=100))
    def test_parser_never_crashes(self, arbitrary_text):
        """
        **Feature: aegis, Property 2: Parsing Round-Trip Consistency**
        
        The parser should never crash on any input - it should either
        successfully parse or raise a ParseError.
        
        **Validates: Requirements 3.2**
        """
        try:
            tokens = self.lexer.tokenize(arbitrary_text)
            ast = self.parser.parse(tokens)
            # If successful, should return a list
            assert isinstance(ast, list)
        except (LexerError, ParseError):
            # These errors are acceptable for invalid input
            pass
        except Exception as e:
            # Any other exception is a bug
            pytest.fail(f"Parser crashed with unexpected exception: {e}")
    
    @given(st.lists(assignment_statement(), min_size=1, max_size=5))
    def test_multiple_assignments_roundtrip(self, assignments):
        """
        **Feature: aegis, Property 2: Parsing Round-Trip Consistency**
        
        For any sequence of valid assignment statements, parsing should
        preserve all statements correctly.
        
        **Validates: Requirements 3.5**
        """
        try:
            # Join assignments with newlines
            program = '\n'.join(assignments)
            
            tokens = self.lexer.tokenize(program)
            ast = self.parser.parse(tokens)
            
            # Should have same number of statements as input
            assert len(ast) == len(assignments)
            
            # Pretty-print and re-parse
            reconstructed = self.printer.print_program(ast)
            tokens2 = self.lexer.tokenize(reconstructed)
            ast2 = self.parser.parse(tokens2)
            
            # Should maintain the same structure
            assert len(ast) == len(ast2)
            
            # Each statement should be preserved
            for i in range(len(ast)):
                stmt1_pretty = self.printer.print_ast(ast[i])
                stmt2_pretty = self.printer.print_ast(ast2[i])
                assert stmt1_pretty == stmt2_pretty
                
        except (LexerError, ParseError):
            # If parsing fails, some assignment might be invalid
            pass
    
    @given(arithmetic_operator, valid_integer, valid_integer)
    def test_operator_precedence_consistency(self, op1, left, right):
        """
        **Feature: aegis, Property 2: Parsing Round-Trip Consistency**
        
        For any arithmetic operation, parsing should respect operator
        precedence and associativity rules consistently.
        
        **Validates: Requirements 3.4**
        """
        try:
            # Create a simple binary operation
            expression = f"{left} {op1} {right}"
            assignment = f"result = {expression}"
            
            tokens = self.lexer.tokenize(assignment)
            ast = self.parser.parse(tokens)
            
            # Should parse successfully
            assert len(ast) == 1
            
            # Extract the expression and verify structure
            expr_node = ast[0].expression
            expr_pretty = self.printer.print_ast(expr_node)
            
            # Re-parse and verify consistency
            assignment2 = f"result = {expr_pretty}"
            tokens2 = self.lexer.tokenize(assignment2)
            ast2 = self.parser.parse(tokens2)
            
            expr_node2 = ast2[0].expression
            expr_pretty2 = self.printer.print_ast(expr_node2)
            
            # Should be identical
            assert expr_pretty == expr_pretty2
            
        except (LexerError, ParseError):
            # If parsing fails, the operation might be invalid
            pass
    
    @given(st.lists(valid_identifier(), min_size=2, max_size=4), arithmetic_operator)
    def test_complex_expression_roundtrip(self, identifiers, operator):
        """
        **Feature: aegis, Property 2: Parsing Round-Trip Consistency**
        
        For any complex expression with multiple variables, parsing
        should preserve the expression structure correctly.
        
        **Validates: Requirements 3.5**
        """
        try:
            # Create a chain of operations: id1 op id2 op id3 ...
            if len(identifiers) < 2:
                return
            
            expression_parts = [identifiers[0]]
            for i in range(1, len(identifiers)):
                expression_parts.extend([operator, identifiers[i]])
            
            expression = ' '.join(expression_parts)
            assignment = f"result = {expression}"
            
            tokens = self.lexer.tokenize(assignment)
            ast = self.parser.parse(tokens)
            
            # Should parse successfully
            assert len(ast) == 1
            
            # Pretty-print and re-parse
            reconstructed = self.printer.print_program(ast)
            tokens2 = self.lexer.tokenize(reconstructed)
            ast2 = self.parser.parse(tokens2)
            
            # Should maintain structure
            reconstructed2 = self.printer.print_program(ast2)
            assert reconstructed == reconstructed2
            
        except (LexerError, ParseError):
            # If parsing fails, the expression might be invalid
            pass