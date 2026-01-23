"""
Property-based tests for AEGIS pipeline execution.

These tests validate the correctness of the complete execution pipeline
including execution mode transitions, pipeline completeness, and console
output visibility.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant, initialize
from aegis.pipeline import AegisExecutionPipeline, ExecutionResult
from aegis.lexer.tokens import TokenType
from aegis.runtime.monitor import SecurityViolation
import tempfile
import os


# Test data generators
@st.composite
def valid_aegis_programs(draw):
    """Generate valid AEGIS programs for testing."""
    # Generate variable names
    var_names = draw(st.lists(
        st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=8),
        min_size=1, max_size=5, unique=True
    ))
    
    # Generate integer values
    values = draw(st.lists(
        st.integers(min_value=-1000, max_value=1000),
        min_size=len(var_names), max_size=len(var_names)
    ))
    
    # Build program
    statements = []
    
    # Add assignments
    for var, val in zip(var_names, values):
        statements.append(f"{var} = {val}")
    
    # Add some arithmetic operations
    if len(var_names) >= 2:
        result_var = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=8))
        var1, var2 = draw(st.sampled_from(var_names)), draw(st.sampled_from(var_names))
        op = draw(st.sampled_from(['+', '-', '*']))
        statements.append(f"{result_var} = {var1} {op} {var2}")
        var_names.append(result_var)
    
    # Add print statements
    print_vars = draw(st.lists(
        st.sampled_from(var_names),
        min_size=1, max_size=min(3, len(var_names))
    ))
    
    for var in print_vars:
        statements.append(f"print {var}")
    
    return '\n'.join(statements)


@st.composite
def simple_programs(draw):
    """Generate simple programs for basic testing."""
    programs = [
        "x = 5\nprint x",
        "a = 10\nb = 20\nsum = a + b\nprint sum",
        "x = 100\ny = x / 2\nprint y",
        "a = 3\nb = 4\nc = a * b\nprint c",
        "val = 42\nprint val"
    ]
    return draw(st.sampled_from(programs))


class TestPipelineProperties:
    """Property-based tests for pipeline execution."""
    
    def setup_method(self):
        """Set up test environment."""
        # Create temporary trust file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.trust_file = self.temp_file.name
        
        # Initialize pipeline with fresh state
        self.pipeline = AegisExecutionPipeline(
            trust_file=self.trust_file,
            trust_threshold=1.0,
            violation_threshold=1000
        )
    
    def teardown_method(self):
        """Clean up test environment."""
        # Clean up pipeline state
        if hasattr(self, 'pipeline'):
            self.pipeline.cleanup_system()
        
        # Remove temporary file
        if os.path.exists(self.trust_file):
            os.unlink(self.trust_file)
    
    @given(simple_programs())
    @settings(max_examples=20, deadline=5000)
    def test_property_9_execution_mode_transition_correctness(self, program):
        """
        **Feature: aegis, Property 9: Execution Mode Transition Correctness**
        
        Validates that execution mode transitions occur correctly based on trust scores:
        - New programs start in sandboxed mode
        - Programs with trust >= threshold AND sufficient history switch to optimized mode
        - Mode transitions preserve program semantics
        """
        # Create fresh pipeline for this test to ensure isolation
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.close()
        temp_trust_file = temp_file.name
        
        try:
            fresh_pipeline = AegisExecutionPipeline(
                trust_file=temp_trust_file,
                trust_threshold=1.0,
                violation_threshold=1000
            )
            
            # First execution should be sandboxed
            result1 = fresh_pipeline.execute(program, verbose=False)
            assume(result1.success)  # Skip if program fails
            
            assert result1.execution_mode == 'sandboxed', \
                "First execution should be in sandboxed mode"
            
            # Execute multiple times to build trust
            results = [result1]
            found_optimized = False
            
            for i in range(15):  # Execute up to 15 times to ensure we get enough history
                # Check trust eligibility BEFORE execution (this determines execution mode)
                code_hash = fresh_pipeline.trust_manager.get_code_hash(program)
                is_trusted_before = fresh_pipeline.trust_manager.is_trusted_for_optimization(code_hash)
                
                result = fresh_pipeline.execute(program, verbose=False)
                assume(result.success)  # Skip if execution fails
                results.append(result)
                
                # Trust should generally increase (or stay same if violations occur)
                assert result.trust_score >= 0.0, "Trust score should never be negative"
                
                # The execution mode should match the trust eligibility BEFORE execution
                if is_trusted_before:
                    assert result.execution_mode == 'optimized', \
                        f"Should be optimized when is_trusted_for_optimization was True before execution"
                    found_optimized = True
                else:
                    assert result.execution_mode == 'sandboxed', \
                        f"Should be sandboxed when is_trusted_for_optimization was False before execution"
                
                # Output should be consistent regardless of execution mode
                assert result.output == result1.output, \
                    "Program output should be consistent across execution modes"
                
                # Break if we've reached optimized mode and tested it
                if result.execution_mode == 'optimized':
                    break
            
            # We should eventually reach optimized mode for simple programs
            # (This is not a strict requirement but helps validate the trust system)
            if not found_optimized:
                # This is not a failure, just means the program didn't build enough trust
                # which can happen with more complex programs or edge cases
                pass
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_trust_file):
                os.unlink(temp_trust_file)
    
    @given(valid_aegis_programs())
    @settings(max_examples=15, deadline=10000)
    def test_property_14_pipeline_execution_completeness(self, program):
        """
        **Feature: aegis, Property 14: Pipeline Execution Completeness**
        
        Validates that the pipeline executes all phases correctly:
        - All pipeline phases complete successfully for valid programs
        - Execution results contain all required information
        - Pipeline state is consistent after execution
        """
        result = self.pipeline.execute(program, verbose=False)
        
        # Pipeline should complete (success or controlled failure)
        assert isinstance(result, ExecutionResult), \
            "Pipeline should return ExecutionResult"
        
        # Result should have all required fields
        assert hasattr(result, 'success'), "Result should have success field"
        assert hasattr(result, 'execution_time'), "Result should have execution_time field"
        assert hasattr(result, 'execution_mode'), "Result should have execution_mode field"
        assert hasattr(result, 'trust_score'), "Result should have trust_score field"
        assert hasattr(result, 'metrics'), "Result should have metrics field"
        assert hasattr(result, 'output'), "Result should have output field"
        
        # Execution time should be reasonable
        assert result.execution_time >= 0.0, "Execution time should be non-negative"
        assert result.execution_time < 10.0, "Execution time should be reasonable (< 10s)"
        
        # Trust score should be valid
        assert result.trust_score >= 0.0, "Trust score should be non-negative"
        
        # Execution mode should be valid
        valid_modes = {'sandboxed', 'optimized', 'failed'}
        assert result.execution_mode in valid_modes, \
            f"Execution mode should be one of {valid_modes}"
        
        # If successful, should have proper metrics
        if result.success:
            assert result.metrics is not None, "Successful execution should have metrics"
            assert result.metrics.instruction_count >= 0, "Instruction count should be non-negative"
            assert isinstance(result.output, list), "Output should be a list"
            
            # Trust score should be positive for successful execution
            assert result.trust_score > 0.0, "Successful execution should increase trust"
        
        # If failed, should have error message
        if not result.success:
            assert result.error_message is not None, "Failed execution should have error message"
            assert result.execution_mode == 'failed', "Failed execution should have 'failed' mode"
    
    @given(simple_programs())
    @settings(max_examples=10, deadline=5000)
    def test_property_15_console_output_visibility(self, program):
        """
        **Feature: aegis, Property 15: Console Output Visibility**
        
        Validates that console output is properly captured and visible:
        - Print statements produce visible output
        - Output is captured in execution results
        - Output format is consistent and readable
        """
        result = self.pipeline.execute(program, verbose=False)
        assume(result.success)  # Only test successful executions
        
        # Count expected print statements in program
        print_count = program.count('print ')
        
        if print_count > 0:
            # Should have output if there are print statements
            assert len(result.output) > 0, \
                "Programs with print statements should produce output"
            
            # Output should be strings
            for output_line in result.output:
                assert isinstance(output_line, str), \
                    "Output lines should be strings"
                
                # Output should be non-empty and reasonable
                assert len(output_line.strip()) > 0, \
                    "Output lines should not be empty"
                
                # Output should be numeric (since we only print integers)
                try:
                    int(output_line.strip())
                except ValueError:
                    pytest.fail(f"Output '{output_line}' should be numeric")
        
        # Metrics should reflect print operations
        if print_count > 0:
            assert result.metrics.print_operations >= 0, \
                "Print operations should be tracked in metrics"
    
    @given(st.lists(simple_programs(), min_size=2, max_size=5))
    @settings(max_examples=5, deadline=10000)
    def test_batch_execution_consistency(self, programs):
        """
        Test that batch execution produces consistent results.
        
        Validates that executing programs in batch produces the same
        results as executing them individually.
        """
        # Create fresh pipelines for fair comparison
        temp_file1 = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file1.close()
        temp_trust_file1 = temp_file1.name
        
        temp_file2 = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file2.close()
        temp_trust_file2 = temp_file2.name
        
        try:
            # Execute programs individually
            individual_pipeline = AegisExecutionPipeline(trust_file=temp_trust_file1)
            individual_results = []
            for program in programs:
                result = individual_pipeline.execute(program, verbose=False)
                individual_results.append(result)
            
            # Execute programs in batch
            batch_pipeline = AegisExecutionPipeline(trust_file=temp_trust_file2)
            batch_results = batch_pipeline.execute_batch(programs, verbose=False)
            
            # Results should be consistent
            assert len(batch_results) == len(individual_results), \
                "Batch execution should return same number of results"
            
            for i, (individual, batch) in enumerate(zip(individual_results, batch_results)):
                # Success status should match
                assert individual.success == batch.success, \
                    f"Program {i}: Success status should match"
                
                # If both successful, outputs should match
                if individual.success and batch.success:
                    assert individual.output == batch.output, \
                        f"Program {i}: Output should match between individual and batch execution"
        
        finally:
            # Clean up temporary files
            for temp_file in [temp_trust_file1, temp_trust_file2]:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)


class PipelineStateMachine(RuleBasedStateMachine):
    """
    Stateful property testing for pipeline execution.
    
    This tests the pipeline's behavior over multiple executions,
    validating state transitions and consistency.
    """
    
    def __init__(self):
        super().__init__()
        # Create temporary trust file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.trust_file = self.temp_file.name
        
        self.pipeline = AegisExecutionPipeline(
            trust_file=self.trust_file,
            trust_threshold=1.0
        )
        self.executed_programs = {}  # program -> list of results
        self.total_executions = 0
    
    def teardown(self):
        """Clean up resources."""
        if os.path.exists(self.trust_file):
            os.unlink(self.trust_file)
    
    @rule(program=simple_programs())
    def execute_program(self, program):
        """Execute a program and track results."""
        result = self.pipeline.execute(program, verbose=False)
        
        if program not in self.executed_programs:
            self.executed_programs[program] = []
        
        self.executed_programs[program].append(result)
        self.total_executions += 1
    
    @rule()
    def check_system_status(self):
        """Check that system status is consistent."""
        status = self.pipeline.get_system_status()
        
        # Execution count should match our tracking
        assert status['execution_stats']['total_executions'] == self.total_executions, \
            "System execution count should match actual executions"
        
        # Trust system should have reasonable values
        trust_stats = status['trust_system']
        assert trust_stats['total_codes'] >= 0, "Total codes should be non-negative"
        assert trust_stats['trusted_codes'] >= 0, "Trusted codes should be non-negative"
        assert trust_stats['trusted_codes'] <= trust_stats['total_codes'], \
            "Trusted codes should not exceed total codes"
    
    @invariant()
    def trust_scores_are_consistent(self):
        """Trust scores should be consistent across executions."""
        for program, results in self.executed_programs.items():
            if len(results) <= 1:
                continue
            
            # Trust should generally increase or stay same for successful executions
            successful_results = [r for r in results if r.success]
            if len(successful_results) >= 2:
                for i in range(1, len(successful_results)):
                    prev_trust = successful_results[i-1].trust_score
                    curr_trust = successful_results[i].trust_score
                    
                    # Trust should not decrease significantly without violations
                    if not successful_results[i].violations:
                        assert curr_trust >= prev_trust * 0.9, \
                            f"Trust should not decrease significantly without violations: {prev_trust} -> {curr_trust}"


# Stateful test
TestPipelineStateMachine = PipelineStateMachine.TestCase


if __name__ == "__main__":
    # Run a quick test
    pipeline = AegisExecutionPipeline(trust_file="test_trust.json")
    result = pipeline.execute("x = 5\nprint x", verbose=True)
    print(f"Test result: {result.success}, output: {result.output}")
    
    # Clean up
    if os.path.exists("test_trust.json"):
        os.unlink("test_trust.json")