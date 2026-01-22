"""
Property-based tests for trust management in AEGIS.

These tests validate that the trust management system correctly handles
trust score lifecycle across all possible execution scenarios and maintains
consistent behavior under various conditions.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from aegis.trust.trust_manager import TrustManager, TrustScore
from aegis.trust.trust_policy import TrustPolicy
from aegis.runtime.monitor import ExecutionMetrics, SecurityViolation
from aegis.interpreter.context import ExecutionContext
import tempfile
import os


class TestTrustManagerProperties:
    """Property-based tests for trust management system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a unique temporary file for each test method
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.trust_manager = TrustManager(trust_file=self.temp_file.name)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        # Ensure clean state after each test
        if hasattr(self, 'temp_file') and os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    @given(st.lists(st.booleans(), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=1000)
    def test_trust_score_lifecycle_management(self, execution_results):
        """
        **Feature: aegis, Property 8: Trust Score Lifecycle Management**
        
        The trust management system must correctly calculate and maintain
        trust scores throughout the complete lifecycle of code execution,
        ensuring that trust increases with successful executions and
        decreases with violations, while maintaining consistency.
        
        **Validates: Requirements 7.1, 7.2, 7.3, 7.4**
        """
        # Create a fresh trust manager for this test to ensure isolation
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.close()
        trust_manager = TrustManager(trust_file=temp_file.name)
        
        try:
            code_hash = f"lifecycle_test_{hash(tuple(execution_results))}_{id(self)}"  # Unique per test
            
            # Track expected behavior
            successful_count = 0
            violation_count = 0
            total_executions = 0
            
            for had_violation in execution_results:
                # Create metrics for this execution
                metrics = ExecutionMetrics()
                metrics.instruction_count = 50  # Efficient execution
                metrics.execution_time = 0.05   # Fast execution
                
                # Update trust based on execution result
                violations = [SecurityViolation("test", "test")] if had_violation else []
                old_score = trust_manager.get_trust_score(code_hash).current_score
                
                new_score = trust_manager.update_trust(code_hash, metrics, violations)
                
                # Update counters
                total_executions += 1
                if had_violation:
                    violation_count += 1
                else:
                    successful_count += 1
                
                # Verify trust score behavior
                trust_score = trust_manager.get_trust_score(code_hash)
                
                # Trust score should be non-negative
                assert trust_score.current_score >= 0.0, "Trust score must be non-negative"
                
                # Trust score should not exceed maximum
                assert trust_score.current_score <= 10.0, "Trust score must not exceed maximum"
                
                # Execution count should match
                assert trust_score.execution_count == total_executions, \
                    f"Execution count should match actual executions: {trust_score.execution_count} != {total_executions}"
                
                # Successful execution count should match
                assert trust_score.successful_executions == successful_count, \
                    f"Successful execution count should match: {trust_score.successful_executions} != {successful_count}"
                
                # Violation count should match
                assert trust_score.violation_count == violation_count, \
                    f"Violation count should match: {trust_score.violation_count} != {violation_count}"
                
                # Trust should increase on success, decrease on violation
                if had_violation:
                    assert new_score <= old_score, "Trust should not increase on violation"
                else:
                    assert new_score >= old_score, "Trust should not decrease on success"
            
            # Final consistency checks
            final_trust = trust_manager.get_trust_score(code_hash)
            
            # Success rate calculation should be correct
            if total_executions > 0:
                expected_success_rate = successful_count / total_executions
                actual_success_rate = final_trust.successful_executions / final_trust.execution_count
                assert abs(actual_success_rate - expected_success_rate) < 0.001, \
                    "Success rate calculation should be accurate"
            
            # Trust level should be consistent with score
            level = final_trust.get_trust_level()
            if final_trust.current_score >= 2.0:
                assert level == "HIGH"
            elif final_trust.current_score >= 1.0:
                assert level == "MEDIUM"
            elif final_trust.current_score >= 0.5:
                assert level == "LOW"
            else:
                assert level == "NONE"
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    @given(st.integers(min_value=1, max_value=10), 
           st.integers(min_value=0, max_value=3))
    @settings(max_examples=15, deadline=1000)
    def test_optimization_eligibility_consistency(self, successful_executions, violations):
        """
        **Feature: aegis, Property 8a: Optimization Eligibility Consistency**
        
        The trust management system must consistently determine optimization
        eligibility based on trust score, execution history, and success rate,
        ensuring that the same conditions always produce the same result.
        """
        # Create a fresh trust manager for this test to ensure isolation
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.close()
        trust_manager = TrustManager(trust_file=temp_file.name)
        
        try:
            code_hash = f"eligibility_test_{successful_executions}_{violations}_{id(self)}"  # Unique per test
            metrics = ExecutionMetrics()
            metrics.instruction_count = 50
            metrics.execution_time = 0.05
            
            # Execute successful runs
            for _ in range(successful_executions):
                trust_manager.update_trust(code_hash, metrics, [])
            
            # Execute violations
            violation = SecurityViolation("test", "test")
            for _ in range(violations):
                trust_manager.update_trust(code_hash, metrics, [violation])
            
            trust_score = trust_manager.get_trust_score(code_hash)
            
            # Check eligibility using both methods
            manager_eligible = trust_manager.is_trusted_for_optimization(code_hash)
            score_eligible = trust_score.is_eligible_for_optimization(trust_manager.trust_threshold)
            
            # Both methods should agree
            assert manager_eligible == score_eligible, \
                "Trust manager and trust score eligibility should agree"
            
            # Verify basic eligibility criteria
            total_executions = successful_executions + violations
            if total_executions > 0:
                success_rate = successful_executions / total_executions
                
                # Basic checks that should always hold
                if trust_score.current_score < trust_manager.trust_threshold:
                    assert not manager_eligible, "Should not be eligible with low trust score"
                
                if total_executions < 3:
                    assert not manager_eligible, "Should not be eligible with insufficient executions"
                
                if success_rate < 0.8:
                    assert not manager_eligible, "Should not be eligible with low success rate"
                
                if not trust_manager.optimization_enabled:
                    assert not manager_eligible, "Should not be eligible when optimization disabled"
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    @given(st.lists(st.text(alphabet="abcdefghijklmnopqrstuvwxyz0123456789", min_size=5, max_size=20), 
                   min_size=2, max_size=5))
    @settings(max_examples=10, deadline=1000)
    def test_multiple_code_trust_isolation(self, code_samples):
        """
        **Feature: aegis, Property 8b: Multiple Code Trust Isolation**
        
        The trust management system must maintain separate and isolated
        trust scores for different pieces of code, ensuring that the
        trust level of one code does not affect another.
        """
        # Create a fresh trust manager for this test to ensure isolation
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.close()
        trust_manager = TrustManager(trust_file=temp_file.name)
        
        try:
            # Make code samples unique
            unique_codes = list(set(code_samples))
            assume(len(unique_codes) >= 2)
            
            code_hashes = [trust_manager.get_code_hash(code) for code in unique_codes]
            
            # Verify all hashes are different
            assert len(set(code_hashes)) == len(unique_codes), \
                "Different code should produce different hashes"
            
            metrics = ExecutionMetrics()
            metrics.instruction_count = 50
            metrics.execution_time = 0.05
            
            # Build different trust levels for different codes
            for i, code_hash in enumerate(code_hashes):
                # Give different numbers of successful executions
                executions = (i % 3) + 1  # 1, 2, or 3 executions
                for _ in range(executions):
                    trust_manager.update_trust(code_hash, metrics, [])
                
                # Add violations to some codes
                if i % 2 == 0:  # Every other code gets a violation
                    violation = SecurityViolation("test", "test")
                    trust_manager.update_trust(code_hash, metrics, [violation])
            
            # Verify trust scores are independent
            trust_scores = [trust_manager.get_trust_score(h) for h in code_hashes]
            
            # Each code should have its own trust score
            for i, trust_score in enumerate(trust_scores):
                assert trust_score.code_hash == code_hashes[i]
                
                # Trust scores should reflect individual execution history
                expected_executions = ((i % 3) + 1) + (1 if i % 2 == 0 else 0)
                assert trust_score.execution_count == expected_executions, \
                    f"Code {i}: expected {expected_executions}, got {trust_score.execution_count}"
                
                # Violation count should be correct
                expected_violations = 1 if i % 2 == 0 else 0
                assert trust_score.violation_count == expected_violations, \
                    f"Code {i}: expected {expected_violations} violations, got {trust_score.violation_count}"
            
            # Modifying one code's trust should not affect others
            first_hash = code_hashes[0]
            other_scores_before = [(h, trust_manager.get_trust_score(h).current_score) 
                                  for h in code_hashes[1:]]
            
            # Add more executions to first code
            for _ in range(3):
                trust_manager.update_trust(first_hash, metrics, [])
            
            # Other scores should be unchanged
            for code_hash, old_score in other_scores_before:
                current_score = trust_manager.get_trust_score(code_hash).current_score
                assert current_score == old_score, \
                    f"Trust score for {code_hash} should not change when other code is executed"
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    @given(st.floats(min_value=0.1, max_value=5.0))
    @settings(max_examples=20)
    def test_trust_threshold_behavior(self, threshold):
        """
        **Feature: aegis, Property 8c: Trust Threshold Behavior**
        
        The trust management system must correctly apply trust thresholds
        for optimization eligibility, ensuring that changes to the threshold
        immediately affect eligibility decisions without corrupting trust scores.
        """
        # Create a fresh trust manager for this test to ensure isolation
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.close()
        trust_manager = TrustManager(trust_file=temp_file.name)
        
        try:
            code_hash = f"threshold_test_{threshold}_{id(self)}"
            metrics = ExecutionMetrics()
            metrics.instruction_count = 50
            metrics.execution_time = 0.05
            
            # Build up significant trust
            for _ in range(15):  # Should reach high trust level
                trust_manager.update_trust(code_hash, metrics, [])
            
            trust_score = trust_manager.get_trust_score(code_hash)
            original_score = trust_score.current_score
            
            # Set the test threshold
            trust_manager.set_trust_threshold(threshold)
            
            # Trust score should not change when threshold changes
            assert trust_score.current_score == original_score, \
                "Trust score should not change when threshold changes"
            
            # Eligibility should reflect new threshold
            expected_eligible = (
                trust_score.current_score >= threshold and
                trust_score.execution_count >= 3 and
                trust_score.successful_executions / trust_score.execution_count >= 0.8 and
                trust_manager.optimization_enabled
            )
            
            actual_eligible = trust_manager.is_trusted_for_optimization(code_hash)
            assert actual_eligible == expected_eligible, \
                f"Eligibility should match threshold: score={original_score:.2f}, threshold={threshold:.2f}"
            
            # Threshold should be properly stored
            assert abs(trust_manager.trust_threshold - threshold) < 0.001, \
                "Trust threshold should be stored correctly"
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    @given(st.integers(min_value=1, max_value=10))
    @settings(max_examples=20)
    def test_trust_persistence_consistency(self, execution_count):
        """
        **Feature: aegis, Property 8d: Trust Persistence Consistency**
        
        The trust management system must correctly persist and restore
        trust data across sessions, ensuring that trust scores and
        execution history are maintained accurately.
        """
        # Create a fresh trust manager for this test to ensure isolation
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.close()
        trust_manager = TrustManager(trust_file=temp_file.name)
        
        try:
            code_hash = f"persistence_test_{execution_count}_{id(self)}"
            metrics = ExecutionMetrics()
            metrics.instruction_count = 75
            metrics.execution_time = 0.08
            
            # Build up trust with some executions
            for i in range(execution_count):
                # Add occasional violations
                violations = [SecurityViolation("test", "test")] if i % 4 == 0 else []
                trust_manager.update_trust(code_hash, metrics, violations)
            
            # Get original trust data
            original_trust = trust_manager.get_trust_score(code_hash)
            original_score = original_trust.current_score
            original_executions = original_trust.execution_count
            original_successful = original_trust.successful_executions
            original_violations = original_trust.violation_count
            
            # Create new trust manager with same file
            new_trust_manager = TrustManager(trust_file=temp_file.name)
            
            # Verify data was loaded correctly
            loaded_trust = new_trust_manager.get_trust_score(code_hash)
            
            assert loaded_trust.current_score == original_score, \
                "Trust score should persist across sessions"
            assert loaded_trust.execution_count == original_executions, \
                "Execution count should persist across sessions"
            assert loaded_trust.successful_executions == original_successful, \
                "Successful execution count should persist across sessions"
            assert loaded_trust.violation_count == original_violations, \
                "Violation count should persist across sessions"
            
            # Eligibility should be the same
            original_eligible = trust_manager.is_trusted_for_optimization(code_hash)
            loaded_eligible = new_trust_manager.is_trusted_for_optimization(code_hash)
            assert original_eligible == loaded_eligible, \
                "Optimization eligibility should persist across sessions"
            
            # Configuration should persist
            assert new_trust_manager.trust_threshold == trust_manager.trust_threshold, \
                "Trust threshold should persist across sessions"
            assert new_trust_manager.optimization_enabled == trust_manager.optimization_enabled, \
                "Optimization enabled flag should persist across sessions"
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)
    
    def test_trust_revocation_completeness(self):
        """
        **Feature: aegis, Property 8e: Trust Revocation Completeness**
        
        The trust management system must completely revoke trust when
        requested, resetting all trust-related state while preserving
        execution history for audit purposes.
        """
        # Create a fresh trust manager for this test to ensure isolation
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        temp_file.close()
        trust_manager = TrustManager(trust_file=temp_file.name)
        
        try:
            code_hash = f"revocation_test_{id(self)}"
            metrics = ExecutionMetrics()
            metrics.instruction_count = 50
            metrics.execution_time = 0.05
            
            # Build up significant trust
            for _ in range(10):
                trust_manager.update_trust(code_hash, metrics, [])
            
            trust_score = trust_manager.get_trust_score(code_hash)
            
            # Verify trust was built up
            assert trust_score.current_score > 0.0
            assert trust_score.execution_count > 0
            assert trust_manager.is_trusted_for_optimization(code_hash)
            
            # Store execution history length
            history_length_before = len(trust_score.trust_history)
            
            # Revoke trust
            trust_manager.revoke_trust(code_hash, "test_revocation")
            
            # Verify trust was completely revoked
            assert trust_score.current_score == 0.0, "Trust score should be reset to zero"
            assert not trust_manager.is_trusted_for_optimization(code_hash), \
                "Code should not be eligible for optimization after revocation"
            
            # Execution history should be preserved (with revocation entry added)
            assert len(trust_score.trust_history) >= history_length_before, \
                "Execution history should be preserved"
            
            # Last entry should record the revocation
            last_entry = trust_score.trust_history[-1]
            assert last_entry.get('reset') == True, "Last entry should record revocation"
            assert last_entry.get('reason') == "test_revocation", "Revocation reason should be recorded"
            
            # Execution counts should be preserved
            assert trust_score.execution_count > 0, "Execution count should be preserved"
            assert trust_score.successful_executions > 0, "Successful execution count should be preserved"
        
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file.name):
                os.unlink(temp_file.name)