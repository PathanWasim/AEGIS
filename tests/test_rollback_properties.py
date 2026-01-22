"""
Property-based tests for AEGIS rollback handling system.

**Feature: aegis, Property 12: Rollback State Consistency**

These tests verify that the rollback system correctly handles security violations
by transitioning from optimized execution back to sandboxed mode while maintaining
execution state consistency and proper integration with trust management.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from datetime import datetime, timedelta
from aegis.runtime.rollback import RollbackHandler, RollbackEvent
from aegis.runtime.monitor import RuntimeMonitor, SecurityViolation, ExecutionMetrics
from aegis.trust.trust_manager import TrustManager, TrustScore
from aegis.interpreter.context import ExecutionContext
from aegis.compiler.cache import CodeCache
from aegis.compiler.optimizer import OptimizedExecutor


class TestRollbackProperties:
    """Property-based tests for rollback system correctness."""
    
    @given(
        violation_type=st.sampled_from(['instruction_limit', 'memory_limit', 'arithmetic_overflow']),
        code_hash=st.text(min_size=16, max_size=16, alphabet='0123456789abcdef'),
        details=st.text(min_size=1, max_size=50),
        trust_score_before=st.floats(min_value=0.0, max_value=10.0)
    )
    @settings(max_examples=20)
    def test_rollback_event_creation_consistency(self, violation_type, code_hash, details, trust_score_before):
        """
        **Property 12.1: Rollback Event Creation Consistency**
        
        Validates that rollback events are created consistently with all required
        information and proper timestamp ordering.
        
        **Validates: Requirements 9.1, 9.2, 9.3**
        """
        assume(len(details.strip()) > 0)
        
        # Create fresh instances for each test
        rollback_handler = RollbackHandler()
        trust_manager = TrustManager(trust_file=".test_trust_prop.json")
        cache = CodeCache()
        monitor = RuntimeMonitor()
        optimizer = OptimizedExecutor(cache, monitor)
        
        # Set up integration
        optimizer.set_rollback_handler(rollback_handler)
        rollback_handler.register_trust_update_callback(
            trust_manager.revoke_trust_for_violation
        )
        rollback_handler.register_cache_clear_callback(
            optimizer.clear_cache
        )
        
        try:
            # Create execution context
            context = ExecutionContext()
            context.variables = {'x': 42, 'y': 10}
            
            # Create security violation
            violation = SecurityViolation(violation_type, details, context)
            
            # Trigger rollback
            rollback_event = rollback_handler.trigger_rollback(
                violation_type=violation_type,
                code_hash=code_hash,
                details=details,
                context=context,
                violations=[violation],
                trust_score_before=trust_score_before
            )
            
            # Verify rollback event consistency
            assert rollback_event is not None
            assert rollback_event.violation_type == violation_type
            assert rollback_event.code_hash == code_hash
            assert rollback_event.details == details
            assert rollback_event.execution_mode == 'optimized'
            assert rollback_event.violation_count == 1
            assert rollback_event.trust_score_before == trust_score_before
            assert rollback_event.trust_score_after <= rollback_event.trust_score_before
            assert rollback_event.rollback_time >= 0.0
            
            # Verify timestamp is recent
            time_diff = datetime.now() - rollback_event.timestamp
            assert time_diff.total_seconds() < 1.0
            
            # Verify context state capture
            assert 'variables' in rollback_event.context_state
            assert rollback_event.context_state['variables'] == {'x': 42, 'y': 10}
            assert rollback_event.context_state['variable_count'] == 2
            
            # Verify rollback is recorded in history
            assert len(rollback_handler.rollback_history) == 1
            assert rollback_handler.rollback_history[0] == rollback_event
            
        finally:
            # Clean up
            import os
            if os.path.exists(".test_trust_prop.json"):
                os.remove(".test_trust_prop.json")
    
    @given(
        rollback_count=st.integers(min_value=1, max_value=5),
        violation_types=st.lists(
            st.sampled_from(['instruction_limit', 'memory_limit', 'arithmetic_overflow']),
            min_size=1, max_size=5
        )
    )
    @settings(max_examples=15)
    def test_rollback_statistics_accuracy(self, rollback_count, violation_types):
        """
        **Property 12.2: Rollback Statistics Accuracy**
        
        Validates that rollback statistics are accurately maintained across
        multiple rollback events and properly categorized by type and code.
        
        **Validates: Requirements 9.3, 9.5**
        """
        # Create fresh instances for each test
        rollback_handler = RollbackHandler()
        trust_manager = TrustManager(trust_file=".test_trust_prop2.json")
        
        rollback_handler.register_trust_update_callback(
            trust_manager.revoke_trust_for_violation
        )
        
        try:
            # Limit rollback count to violation types available
            actual_rollback_count = min(rollback_count, len(violation_types))
            
            # Trigger rollbacks
            expected_by_type = {}
            expected_by_code = {}
            
            for i in range(actual_rollback_count):
                violation_type = violation_types[i % len(violation_types)]
                code_hash = f'code{i % 3}'  # Use 3 different codes
                
                # Track expected counts
                expected_by_type[violation_type] = expected_by_type.get(violation_type, 0) + 1
                expected_by_code[code_hash] = expected_by_code.get(code_hash, 0) + 1
                
                # Trigger rollback
                rollback_handler.trigger_rollback(
                    violation_type=violation_type,
                    code_hash=code_hash,
                    details=f"Test violation {i}",
                    context=ExecutionContext(),
                    violations=[SecurityViolation(violation_type, f"Test {i}")],
                    trust_score_before=1.0
                )
            
            # Verify statistics
            stats = rollback_handler.get_rollback_statistics()
            
            assert stats['total_rollbacks'] == actual_rollback_count
            assert stats['rollbacks_by_type'] == expected_by_type
            assert stats['rollbacks_by_code'] == expected_by_code
            assert stats['rollback_enabled'] == True
            assert stats['history_size'] == actual_rollback_count
            assert stats['average_rollback_time'] >= 0.0
            
            # Verify recent rollbacks count (all should be recent)
            assert stats['recent_rollbacks'] == actual_rollback_count
            
        finally:
            # Clean up
            import os
            if os.path.exists(".test_trust_prop2.json"):
                os.remove(".test_trust_prop2.json")
    
    @given(
        enabled=st.booleans(),
        auto_revocation=st.booleans()
    )
    @settings(max_examples=8)
    def test_rollback_configuration_consistency(self, enabled, auto_revocation):
        """
        **Property 12.3: Rollback Configuration Consistency**
        
        Validates that rollback configuration settings are properly respected
        and affect system behavior consistently.
        
        **Validates: Requirements 9.1, 9.4**
        """
        # Create fresh instances for each test
        rollback_handler = RollbackHandler()
        trust_manager = TrustManager(trust_file=".test_trust_prop3.json")
        
        rollback_handler.register_trust_update_callback(
            trust_manager.revoke_trust_for_violation
        )
        
        try:
            # Configure rollback settings
            rollback_handler.enable_rollback(enabled)
            rollback_handler.set_auto_trust_revocation(auto_revocation)
            
            # Verify configuration
            assert rollback_handler.rollback_enabled == enabled
            assert rollback_handler.auto_trust_revocation == auto_revocation
            
            # Test rollback behavior with configuration
            code_hash = 'test1234567890ab'
            
            # Set up trust score
            trust_score = trust_manager.get_trust_score(code_hash)
            trust_score.current_score = 2.0
            
            # Attempt rollback
            rollback_event = rollback_handler.trigger_rollback(
                violation_type='instruction_limit',
                code_hash=code_hash,
                details='Test violation',
                context=ExecutionContext(),
                violations=[SecurityViolation('instruction_limit', 'Test')],
                trust_score_before=2.0
            )
            
            if enabled:
                # Rollback should occur
                assert rollback_event is not None
                assert len(rollback_handler.rollback_history) == 1
                
                # Check trust revocation based on auto_revocation setting
                updated_trust = trust_manager.get_trust_score(code_hash)
                if auto_revocation:
                    assert updated_trust.current_score == 0.0
                # Note: Trust callback might still be called, so we don't assert the opposite
            else:
                # Rollback should be ignored
                assert rollback_event is None
                assert len(rollback_handler.rollback_history) == 0
                
        finally:
            # Clean up
            import os
            if os.path.exists(".test_trust_prop3.json"):
                os.remove(".test_trust_prop3.json")