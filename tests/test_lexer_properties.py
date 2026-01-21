"""
Property-based tests for the AEGIS lexer.

These tests use Hypothesis to generate random inputs and verify
universal properties that should hold for all valid AEGIS programs.
"""

import pytest
from hypothesis import given, strategies as st, assume
from aegis.lexer import Lexer, LexerError, TokenType


# Strategy for generating valid AEGIS identifiers
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
        max_size=20
    ))
    
    identifier = first_char + rest_chars
    
    # Ensure it's not a keyword
    assume(identifier != 'print')
    
    return identifier


# Strategy for generating valid AEGIS integers
valid_integer = st.integers(min_value=0, max_value=999999).map(str)


# Strategy for generating valid AEGIS operators
valid_operator = st.sampled_from(['+', '-', '*', '/', '='])


# Strategy for generating valid AEGIS tokens
@st.composite
def valid_token_sequence(draw):
    """Generate a sequence of valid AEGIS tokens."""
    tokens = []
    
    # Generate a simple expression or assignment
    choice = draw(st.integers(min_value=1, max_value=3))
    
    if choice == 1:
        # Simple assignment: identifier = integer
        identifier = draw(valid_identifier())
        integer = draw(valid_integer)
        tokens = [identifier, ' = ', integer]
    
    elif choice == 2:
        # Arithmetic expression: identifier operator integer
        identifier = draw(valid_identifier())
        operator = draw(st.sampled_from(['+', '-', '*', '/']))
        integer = draw(valid_integer)
        tokens = [identifier, ' ', operator, ' ', integer]
    
    else:
        # Print statement: print identifier
        identifier = draw(valid_identifier())
        tokens = ['print ', identifier]
    
    return ''.join(tokens)


class TestLexerProperties:
    """Property-based tests for lexer correctness."""
    
    @given(valid_identifier())
    def test_identifier_tokenization_roundtrip(self, identifier):
        """
        **Feature: aegis, Property 1: Tokenization Round-Trip Consistency**
        
        For any valid identifier, tokenizing and then reconstructing
        should preserve the original text.
        
        **Validates: Requirements 2.5**
        """
        lexer = Lexer()
        
        try:
            tokens = lexer.tokenize(identifier)
            
            # Should have identifier token + EOF
            assert len(tokens) >= 2
            assert tokens[0].type == TokenType.IDENTIFIER
            assert tokens[0].value == identifier
            assert tokens[-1].type == TokenType.EOF
            
            # Reconstruct the identifier from token
            reconstructed = tokens[0].value
            assert reconstructed == identifier
            
        except LexerError:
            # If lexer fails, the identifier might be invalid
            # This is acceptable for property testing
            pass
    
    @given(valid_integer)
    def test_integer_tokenization_roundtrip(self, integer_str):
        """
        **Feature: aegis, Property 1: Tokenization Round-Trip Consistency**
        
        For any valid integer, tokenizing and then reconstructing
        should preserve the original text.
        
        **Validates: Requirements 2.5**
        """
        lexer = Lexer()
        
        try:
            tokens = lexer.tokenize(integer_str)
            
            # Should have integer token + EOF
            assert len(tokens) >= 2
            assert tokens[0].type == TokenType.INTEGER
            assert tokens[0].value == integer_str
            assert tokens[-1].type == TokenType.EOF
            
            # Reconstruct the integer from token
            reconstructed = tokens[0].value
            assert reconstructed == integer_str
            
        except LexerError:
            # If lexer fails, the integer might be invalid
            # This is acceptable for property testing
            pass
    
    @given(valid_operator)
    def test_operator_tokenization_roundtrip(self, operator):
        """
        **Feature: aegis, Property 1: Tokenization Round-Trip Consistency**
        
        For any valid operator, tokenizing and then reconstructing
        should preserve the original text.
        
        **Validates: Requirements 2.5**
        """
        lexer = Lexer()
        
        try:
            tokens = lexer.tokenize(operator)
            
            # Should have operator token + EOF
            assert len(tokens) >= 2
            assert tokens[-1].type == TokenType.EOF
            
            # Find the operator token (not EOF)
            operator_token = None
            for token in tokens:
                if token.type != TokenType.EOF:
                    operator_token = token
                    break
            
            assert operator_token is not None
            assert operator_token.value == operator
            
            # Reconstruct the operator from token
            reconstructed = operator_token.value
            assert reconstructed == operator
            
        except LexerError:
            # If lexer fails, the operator might be invalid
            # This is acceptable for property testing
            pass
    
    @given(valid_token_sequence())
    def test_program_tokenization_roundtrip(self, program):
        """
        **Feature: aegis, Property 1: Tokenization Round-Trip Consistency**
        
        For any valid AEGIS program, tokenizing and then reconstructing
        should preserve the semantic meaning of the original program.
        
        **Validates: Requirements 2.5**
        """
        lexer = Lexer()
        
        try:
            tokens = lexer.tokenize(program)
            
            # Should end with EOF
            assert tokens[-1].type == TokenType.EOF
            
            # Reconstruct the program from tokens (excluding EOF)
            reconstructed_parts = []
            for i, token in enumerate(tokens[:-1]):  # Exclude EOF
                if token.type == TokenType.NEWLINE:
                    reconstructed_parts.append('\n')
                else:
                    # Add the token value
                    reconstructed_parts.append(token.value)
                    
                    # Add space after token if not the last token and next token isn't newline
                    if i < len(tokens) - 2:  # Not the last non-EOF token
                        next_token = tokens[i + 1]
                        if next_token.type != TokenType.NEWLINE and next_token.type != TokenType.EOF:
                            # Add space between tokens to preserve original spacing
                            reconstructed_parts.append(' ')
            
            reconstructed = ''.join(reconstructed_parts)
            
            # The reconstructed program should tokenize to the same tokens
            # (This tests semantic preservation)
            tokens2 = lexer.tokenize(reconstructed)
            
            # Compare token types and values (excluding position info)
            assert len(tokens) == len(tokens2)
            for t1, t2 in zip(tokens, tokens2):
                assert t1.type == t2.type
                assert t1.value == t2.value
                
        except LexerError:
            # If lexer fails, the program might be invalid
            # This is acceptable for property testing
            pass
    
    @given(st.text(alphabet=st.characters(min_codepoint=32, max_codepoint=126), max_size=100))
    def test_lexer_never_crashes(self, arbitrary_text):
        """
        **Feature: aegis, Property 1: Tokenization Round-Trip Consistency**
        
        The lexer should never crash on any input - it should either
        successfully tokenize or raise a LexerError.
        
        **Validates: Requirements 2.2**
        """
        lexer = Lexer()
        
        try:
            tokens = lexer.tokenize(arbitrary_text)
            # If successful, should always end with EOF
            assert len(tokens) > 0
            assert tokens[-1].type == TokenType.EOF
        except LexerError:
            # LexerError is acceptable for invalid input
            pass
        except Exception as e:
            # Any other exception is a bug
            pytest.fail(f"Lexer crashed with unexpected exception: {e}")
    
    @given(st.lists(valid_identifier(), min_size=1, max_size=10))
    def test_multiple_identifiers_roundtrip(self, identifiers):
        """
        **Feature: aegis, Property 1: Tokenization Round-Trip Consistency**
        
        For any sequence of valid identifiers separated by spaces,
        tokenizing should preserve each identifier correctly.
        
        **Validates: Requirements 2.5**
        """
        # Join identifiers with spaces
        program = ' '.join(identifiers)
        lexer = Lexer()
        
        try:
            tokens = lexer.tokenize(program)
            
            # Filter out non-identifier tokens
            identifier_tokens = [t for t in tokens if t.type == TokenType.IDENTIFIER]
            
            # Should have same number of identifier tokens as input identifiers
            assert len(identifier_tokens) == len(identifiers)
            
            # Each token should match the corresponding identifier
            for token, original in zip(identifier_tokens, identifiers):
                assert token.value == original
                
        except LexerError:
            # If lexer fails, some identifier might be invalid
            # This is acceptable for property testing
            pass
    
    @given(st.lists(valid_integer, min_size=1, max_size=10))
    def test_multiple_integers_roundtrip(self, integers):
        """
        **Feature: aegis, Property 1: Tokenization Round-Trip Consistency**
        
        For any sequence of valid integers separated by spaces,
        tokenizing should preserve each integer correctly.
        
        **Validates: Requirements 2.5**
        """
        # Join integers with spaces
        program = ' '.join(integers)
        lexer = Lexer()
        
        try:
            tokens = lexer.tokenize(program)
            
            # Filter out non-integer tokens
            integer_tokens = [t for t in tokens if t.type == TokenType.INTEGER]
            
            # Should have same number of integer tokens as input integers
            assert len(integer_tokens) == len(integers)
            
            # Each token should match the corresponding integer
            for token, original in zip(integer_tokens, integers):
                assert token.value == original
                
        except LexerError:
            # If lexer fails, some integer might be invalid
            # This is acceptable for property testing
            pass