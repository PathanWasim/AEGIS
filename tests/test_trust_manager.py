"""
Unit tests for trust management system in AEGIS.

These tests verify the trust score calculation, lifecycle management,
and optimization eligibility determination.
"""

import pytest
import tempfile
import os
from datetime import datetime, timedelta
from aegis.trust.trust_manager import TrustManager, TrustScore
from aegis.trust.trust_policy import TrustPolicy
from aegis.runtime.monitor import ExecutionMetrics, SecurityViolation
from aegis.interpreter.context import ExecutionContext


class TestTrustScore:
    """Unit tests for TrustScore class."""
    
    def test_trust_score_creation(self):
        """Test basic trust score creation."""
        trust_score = TrustScore(code_hash="test123")
        
        assert trust_score.code_hash == "test123"
        assert trust_score.current_score == 0.0
        assert trust_score.execution_count == 0
        assert trust_score.successful_executions == 0
        assert trust_score.violation_count == 0
        assert trust_score.last_execution is None
        assert trust_score.last_violation is None
        assert trust_score.first_execution is None
        assert len(trust_score.trust_history) == 0
    
    def test_successful_execution_increases_trust(self):
        """Test that successful executions increase trust score."""
        trust_score = TrustScore(code_hash="test123")
        metrics = ExecutionMetrics()
        metrics.instruction_count = 50
        metrics.execution_time = 0.05
        
        trust_score.add_execution_result(metrics, had_violations=False)
        
        assert trust_score.current_score > 0.0
        assert trust_score.execution_count == 1
        assert trust_score.successful_executions == 1
        assert trust_score.violation_count == 0
        assert trust_score.last_execution is not None
        assert trust_score.first_execution is not None
        assert len(trust_score.trust_history) == 1
    
    def test_violations_decrease_trust(self):
        """Test that violations decrease trust score."""
        trust_score = TrustScore(code_hash="test123")
        
        # First build up some trust
        metrics = ExecutionMetrics()
        metrics.instruction_count = 50
        for _ in range(3):
            trust_score.add_execution_result(metrics, had_violations=False)
        
        initial_score = trust_score.current_score
        
        # Now add a violation
        trust_score.add_execution_result(metrics, had_violations=True)
        
        assert trust_score.current_score < initial_score
        assert trust_score.violation_count == 1
        assert trust_score.last_violation is not None
    
    def test_trust_level_names(self):
        """Test trust level name assignment."""
        trust_score = TrustScore(code_hash="test123")
        
        trust_score.current_score = 0.0
        assert trust_score.get_trust_level() == "NONE"
        
        trust_score.current_score = 0.7
        assert trust_score.get_trust_level() == "LOW"
        
        trust_score.current_score = 1.5
        assert trust_score.get_trust_level() == "MEDIUM"
        
        trust_score.current_score = 2.5
        assert trust_score.get_trust_level() == "HIGH"
    
    def test_optimization_eligibility(self):
        """Test optimization eligibility logic."""
        trust_score = TrustScore(code_hash="test123")
        metrics = ExecutionMetrics()
        metrics.instruction_count = 50  # Efficient execution for bonus
        metrics.execution_time = 0.05   # Fast execution for bonus
        
        # Not eligible initially
        assert not trust_score.is_eligible_for_optimization()
        
        # Build up trust with successful executions (need more to reach 1.0)
        for _ in range(8):  # 8 * 0.14 = 1.12, should be enough
            trust_score.add_execution_result(metrics, had_violations=False)
        
        # Should be eligible now
        assert trust_score.is_eligible_for_optimization()
        
        # Add a violation - should still be eligible if score is high enough
        trust_score.add_execution_result(metrics, had_violations=True)
        
        # Eligibility depends on score and success rate
        success_rate = trust_score.successful_executions / trust_score.execution_count
        eligible = (trust_score.current_score >= 1.0 and 
                   trust_score.execution_count >= 3 and
                   success_rate >= 0.8)
        
        assert trust_score.is_eligible_for_optimization() == eligible
    
    def test_trust_reset(self):
        """Test trust score reset functionality."""
        trust_score = TrustScore(code_hash="test123")
        metrics = ExecutionMetrics()
        
        # Build up some trust
        for _ in range(3):
            trust_score.add_execution_result(metrics, had_violations=False)
        
        assert trust_score.current_score > 0.0
        
        # Reset trust
        trust_score.reset_trust("test_reset")
        
        assert trust_score.current_score == 0.0
        # History should record the reset
        assert any(entry.get('reset') for entry in trust_score.trust_history)
    
    def test_serialization(self):
        """Test trust score serialization and deserialization."""
        trust_score = TrustScore(code_hash="test123")
        metrics = ExecutionMetrics()
        
        # Add some execution history
        trust_score.add_execution_result(metrics, had_violations=False)
        trust_score.add_execution_result(metrics, had_violations=True)
        
        # Serialize to dict
        data = trust_score.to_dict()
        
        # Deserialize from dict
        restored_score = TrustScore.from_dict(data)
        
        assert restored_score.code_hash == trust_score.code_hash
        assert restored_score.current_score == trust_score.current_score
        assert restored_score.execution_count == trust_score.execution_count
        assert restored_score.successful_executions == trust_score.successful_executions
        assert restored_score.violation_count == trust_score.violation_count


class TestTrustManager:
    """Unit tests for TrustManager class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Use temporary file for trust data
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.trust_manager = TrustManager(trust_file=self.temp_file.name)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_trust_manager_creation(self):
        """Test basic trust manager creation."""
        assert self.trust_manager.trust_threshold == 1.0
        assert self.trust_manager.optimization_enabled == True
        assert len(self.trust_manager.trust_scores) == 0
    
    def test_code_hash_generation(self):
        """Test code hash generation."""
        code1 = "x = 5\nprint x"
        code2 = "y = 10\nprint y"
        code3 = "x = 5\nprint x"  # Same as code1
        
        hash1 = self.trust_manager.get_code_hash(code1)
        hash2 = self.trust_manager.get_code_hash(code2)
        hash3 = self.trust_manager.get_code_hash(code3)
        
        assert hash1 != hash2  # Different code should have different hashes
        assert hash1 == hash3  # Same code should have same hash
        assert len(hash1) == 16  # Hash should be truncated to 16 characters
    
    def test_trust_score_retrieval(self):
        """Test trust score retrieval and creation."""
        code_hash = "test123"
        
        # First retrieval should create new trust score
        trust_score = self.trust_manager.get_trust_score(code_hash)
        assert trust_score.code_hash == code_hash
        assert trust_score.current_score == 0.0
        
        # Second retrieval should return same object
        trust_score2 = self.trust_manager.get_trust_score(code_hash)
        assert trust_score is trust_score2
    
    def test_trust_update_successful_execution(self):
        """Test trust update for successful execution."""
        code_hash = "test123"
        metrics = ExecutionMetrics()
        metrics.instruction_count = 50
        metrics.execution_time = 0.05
        
        # Update trust with successful execution
        new_score = self.trust_manager.update_trust(code_hash, metrics, [])
        
        assert new_score > 0.0
        trust_score = self.trust_manager.get_trust_score(code_hash)
        assert trust_score.current_score == new_score
        assert trust_score.execution_count == 1
        assert trust_score.successful_executions == 1
        assert trust_score.violation_count == 0
    
    def test_trust_update_with_violations(self):
        """Test trust update with security violations."""
        code_hash = "test123"
        metrics = ExecutionMetrics()
        
        # First build up some trust
        for _ in range(3):
            self.trust_manager.update_trust(code_hash, metrics, [])
        
        initial_score = self.trust_manager.get_trust_score(code_hash).current_score
        
        # Add violation
        violation = SecurityViolation("test_violation", "Test violation")
        new_score = self.trust_manager.update_trust(code_hash, metrics, [violation])
        
        assert new_score < initial_score
        trust_score = self.trust_manager.get_trust_score(code_hash)
        assert trust_score.violation_count == 1
    
    def test_optimization_eligibility(self):
        """Test optimization eligibility determination."""
        code_hash = "test123"
        metrics = ExecutionMetrics()
        metrics.instruction_count = 50  # Efficient execution for bonus
        metrics.execution_time = 0.05   # Fast execution for bonus
        
        # Initially not trusted
        assert not self.trust_manager.is_trusted_for_optimization(code_hash)
        
        # Build up trust with successful executions (need more to reach 1.0)
        for _ in range(8):  # 8 * 0.14 = 1.12, should be enough
            self.trust_manager.update_trust(code_hash, metrics, [])
        
        # Should be trusted now
        assert self.trust_manager.is_trusted_for_optimization(code_hash)
        
        # Disable optimization globally
        self.trust_manager.enable_optimization(False)
        assert not self.trust_manager.is_trusted_for_optimization(code_hash)
        
        # Re-enable optimization
        self.trust_manager.enable_optimization(True)
        assert self.trust_manager.is_trusted_for_optimization(code_hash)
    
    def test_trust_revocation(self):
        """Test trust revocation."""
        code_hash = "test123"
        metrics = ExecutionMetrics()
        metrics.instruction_count = 50  # Efficient execution for bonus
        metrics.execution_time = 0.05   # Fast execution for bonus
        
        # Build up trust (need more to reach 1.0)
        for _ in range(8):
            self.trust_manager.update_trust(code_hash, metrics, [])
        
        assert self.trust_manager.is_trusted_for_optimization(code_hash)
        
        # Revoke trust
        self.trust_manager.revoke_trust(code_hash, "test_revocation")
        
        assert not self.trust_manager.is_trusted_for_optimization(code_hash)
        trust_score = self.trust_manager.get_trust_score(code_hash)
        assert trust_score.current_score == 0.0
    
    def test_trust_threshold_adjustment(self):
        """Test trust threshold adjustment."""
        code_hash = "test123"
        metrics = ExecutionMetrics()
        metrics.instruction_count = 50  # Efficient execution for bonus
        metrics.execution_time = 0.05   # Fast execution for bonus
        
        # Build up moderate trust (need enough to reach 1.0)
        for _ in range(8):
            self.trust_manager.update_trust(code_hash, metrics, [])
        
        # Should be trusted with default threshold
        assert self.trust_manager.is_trusted_for_optimization(code_hash)
        
        # Raise threshold
        self.trust_manager.set_trust_threshold(2.0)
        
        # Should no longer be trusted
        assert not self.trust_manager.is_trusted_for_optimization(code_hash)
        
        # Lower threshold
        self.trust_manager.set_trust_threshold(0.5)
        
        # Should be trusted again
        assert self.trust_manager.is_trusted_for_optimization(code_hash)
    
    def test_trust_summary(self):
        """Test trust summary generation."""
        # Initially empty
        summary = self.trust_manager.get_trust_summary()
        assert summary['total_codes'] == 0
        assert summary['trusted_codes'] == 0
        assert summary['average_score'] == 0.0
        
        # Add some trust scores
        metrics = ExecutionMetrics()
        
        # Code 1: High trust
        for _ in range(10):
            self.trust_manager.update_trust("code1", metrics, [])
        
        # Code 2: Low trust
        for _ in range(2):
            self.trust_manager.update_trust("code2", metrics, [])
        
        # Code 3: No trust (violations)
        violation = SecurityViolation("test", "test")
        self.trust_manager.update_trust("code3", metrics, [violation])
        
        summary = self.trust_manager.get_trust_summary()
        assert summary['total_codes'] == 3
        assert summary['trusted_codes'] >= 1  # At least code1 should be trusted
        assert summary['average_score'] > 0.0
        assert 'trust_levels' in summary
    
    def test_persistence(self):
        """Test trust data persistence."""
        code_hash = "test123"
        metrics = ExecutionMetrics()
        
        # Build up trust
        for _ in range(3):
            self.trust_manager.update_trust(code_hash, metrics, [])
        
        original_score = self.trust_manager.get_trust_score(code_hash).current_score
        
        # Create new trust manager with same file
        new_trust_manager = TrustManager(trust_file=self.temp_file.name)
        
        # Should load the same trust data
        loaded_score = new_trust_manager.get_trust_score(code_hash).current_score
        assert loaded_score == original_score
    
    def test_cleanup_old_trust_data(self):
        """Test cleanup of old trust data."""
        metrics = ExecutionMetrics()
        
        # Add some trust scores
        self.trust_manager.update_trust("code1", metrics, [])
        self.trust_manager.update_trust("code2", metrics, [])
        
        # Manually set old execution date for code1
        trust_score = self.trust_manager.get_trust_score("code1")
        trust_score.last_execution = datetime.now() - timedelta(days=35)
        
        # Cleanup old data (30 days)
        self.trust_manager.cleanup_old_trust_data(30)
        
        # code1 should be removed, code2 should remain
        assert "code1" not in self.trust_manager.trust_scores
        assert "code2" in self.trust_manager.trust_scores


class TestTrustPolicy:
    """Unit tests for TrustPolicy class."""
    
    def test_default_policy_values(self):
        """Test default policy values."""
        policy = TrustPolicy()
        
        assert policy.TRUST_THRESHOLD_OPTIMIZATION == 1.0
        assert policy.TRUST_INCREMENT_BASE == 0.1
        assert policy.TRUST_DECREMENT_VIOLATION == 0.5
        assert policy.MIN_EXECUTIONS_FOR_OPTIMIZATION == 3
        assert policy.MIN_SUCCESS_RATE == 0.8
    
    def test_trust_score_validation(self):
        """Test trust score validation."""
        policy = TrustPolicy()
        
        assert policy.validate_trust_score(-1.0) == 0.0  # Clamp to minimum
        assert policy.validate_trust_score(15.0) == 10.0  # Clamp to maximum
        assert policy.validate_trust_score(5.0) == 5.0   # Valid score unchanged
    
    def test_trust_increment_calculation(self):
        """Test trust increment calculation."""
        policy = TrustPolicy()
        
        # Basic increment
        increment = policy.calculate_trust_increment(1, 1, 200, 0.2)
        assert increment == policy.TRUST_INCREMENT_BASE
        
        # With bonuses
        increment = policy.calculate_trust_increment(10, 8, 50, 0.05)
        expected = (policy.TRUST_INCREMENT_BASE + 
                   policy.TRUST_INCREMENT_BONUS_CONSISTENT +
                   policy.TRUST_INCREMENT_BONUS_EFFICIENT +
                   policy.TRUST_INCREMENT_BONUS_FAST)
        assert increment == expected
    
    def test_trust_decrement_calculation(self):
        """Test trust decrement calculation."""
        policy = TrustPolicy()
        
        # First violation
        decrement = policy.calculate_trust_decrement(1)
        assert decrement == policy.TRUST_DECREMENT_VIOLATION
        
        # Repeated violations
        decrement = policy.calculate_trust_decrement(3)
        expected = (policy.TRUST_DECREMENT_VIOLATION + 
                   policy.TRUST_DECREMENT_REPEATED * 2)
        assert decrement == expected
    
    def test_optimization_eligibility_policy(self):
        """Test optimization eligibility policy."""
        policy = TrustPolicy()
        
        # Not eligible - low score
        assert not policy.is_eligible_for_optimization(0.5, 5, 4)
        
        # Not eligible - insufficient executions
        assert not policy.is_eligible_for_optimization(1.5, 2, 2)
        
        # Not eligible - low success rate
        assert not policy.is_eligible_for_optimization(1.5, 10, 5)
        
        # Eligible - meets all criteria
        assert policy.is_eligible_for_optimization(1.5, 10, 9)
    
    def test_trust_level_names(self):
        """Test trust level name assignment."""
        policy = TrustPolicy()
        
        assert policy.get_trust_level_name(0.0) == "NONE"
        assert policy.get_trust_level_name(0.7) == "LOW"
        assert policy.get_trust_level_name(1.5) == "MEDIUM"
        assert policy.get_trust_level_name(2.5) == "HIGH"
    
    def test_custom_policy_creation(self):
        """Test custom policy creation."""
        custom_policy = TrustPolicy.create_custom_policy(
            trust_threshold_optimization=2.0,
            min_executions_for_optimization=5
        )
        
        assert custom_policy.TRUST_THRESHOLD_OPTIMIZATION == 2.0
        assert custom_policy.MIN_EXECUTIONS_FOR_OPTIMIZATION == 5
        # Other values should remain default
        assert custom_policy.TRUST_INCREMENT_BASE == 0.1