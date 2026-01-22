"""
Unit tests for AEGIS rollback handling system.

These tests verify the basic functionality of the rollback system
without property-based testing complexity.
"""

import pytest
from datetime import datetime
from aegis.runtime.rollback import RollbackHandler, RollbackEvent
from aegis.runtime.monitor import RuntimeMonitor, SecurityViolation, ExecutionMetrics
from aegis.trust.trust_manager import TrustManager, TrustScore
from aegis.interpreter.context import ExecutionContext
from aegis.compiler.cache import CodeCache
from aegis.compiler.optimizer import OptimizedExecutor


class TestRollbackUnit:
    """Unit tests for rollback system functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rollback_handler = RollbackHandler()
        self.monitor = RuntimeMonitor()
        self.trust_manager = TrustManager(trust_file=".test_trust.json")
        self.cache = CodeCache()
        self.optimizer = OptimizedExecutor(self.cache, self.monitor)
        
        # Set up integration
        self.optimizer.set_rollback_handler(self.rollback_handler)
        self.rollback_handler.register_trust_update_callback(
            self.trust_manager.revoke_trust_for_violation
        )
        self.rollback_handler.register_cache_clear_callback(
            self.optimizer.clear_cache
        )
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import os
        if os.path.exists(".test_trust.json"):
            os.remove(".test_trust.json")
    
    def test_basic_rollback_event_creation(self):
        """Test basic rollback event creation."""
        # Create execution context
        context = ExecutionContext()
        context.variables = {'x': 42, 'y': 10}
        
        # Create security violation
        violation = SecurityViolation('instruction_limit', 'Test violation', context)
        
        # Trigger rollback
        rollback_event = self.rollback_handler.trigger_rollback(
            violation_type='instruction_limit',
            code_hash='test1234567890ab',
            details='Test violation',
            context=context,
            violations=[violation],
            trust_score_before=2.0
        )
        
        # Verify rollback event
        assert rollback_event is not None
        assert rollback_event.violation_type == 'instruction_limit'
        assert rollback_event.code_hash == 'test1234567890ab'
        assert rollback_event.details == 'Test violation'
        assert rollback_event.execution_mode == 'optimized'
        assert rollback_event.violation_count == 1
        assert rollback_event.trust_score_before == 2.0
        assert rollback_event.trust_score_after <= rollback_event.trust_score_before
        assert rollback_event.rollback_time >= 0.0
        
        # Verify context state capture
        assert 'variables' in rollback_event.context_state
        assert rollback_event.context_state['variables'] == {'x': 42, 'y': 10}
        assert rollback_event.context_state['variable_count'] == 2
        
        # Verify rollback is recorded in history
        assert len(self.rollback_handler.rollback_history) == 1
        assert self.rollback_handler.rollback_history[0] == rollback_event
    
    def test_rollback_statistics_tracking(self):
        """Test rollback statistics tracking."""
        # Trigger multiple rollbacks
        violations = [
            ('instruction_limit', 'code1'),
            ('memory_limit', 'code2'),
            ('instruction_limit', 'code1'),
            ('arithmetic_overflow', 'code3')
        ]
        
        for violation_type, code_hash in violations:
            self.rollback_handler.trigger_rollback(
                violation_type=violation_type,
                code_hash=code_hash,
                details=f'Test {violation_type}',
                context=ExecutionContext(),
                violations=[SecurityViolation(violation_type, 'Test')],
                trust_score_before=1.0
            )
        
        # Verify statistics
        stats = self.rollback_handler.get_rollback_statistics()
        
        assert stats['total_rollbacks'] == 4
        assert stats['rollbacks_by_type']['instruction_limit'] == 2
        assert stats['rollbacks_by_type']['memory_limit'] == 1
        assert stats['rollbacks_by_type']['arithmetic_overflow'] == 1
        assert stats['rollbacks_by_code']['code1'] == 2
        assert stats['rollbacks_by_code']['code2'] == 1
        assert stats['rollbacks_by_code']['code3'] == 1
        assert stats['rollback_enabled'] == True
        assert stats['history_size'] == 4
        assert stats['average_rollback_time'] >= 0.0
    
    def test_trust_integration(self):
        """Test rollback integration with trust management."""
        code_hash = 'test1234567890ab'
        
        # Set up initial trust score
        trust_score = self.trust_manager.get_trust_score(code_hash)
        trust_score.current_score = 2.5
        trust_score.execution_count = 5
        trust_score.successful_executions = 4
        
        # Add cache entry
        from aegis.ast.nodes import IntegerNode
        self.cache.put(code_hash, [IntegerNode(42)], [IntegerNode(42)], 0.001, {})
        
        # Verify cache has entry
        assert self.cache.get(code_hash) is not None
        
        # Trigger rollback
        violation = SecurityViolation('instruction_limit', 'Test violation')
        
        rollback_event = self.rollback_handler.trigger_rollback(
            violation_type='instruction_limit',
            code_hash=code_hash,
            details='Test violation',
            context=ExecutionContext(),
            violations=[violation],
            trust_score_before=trust_score.current_score
        )
        
        # Verify trust score was reset
        updated_trust = self.trust_manager.get_trust_score(code_hash)
        assert updated_trust.current_score == 0.0
        
        # Verify cache was cleared
        assert self.cache.get(code_hash) is None
        
        # Verify rollback event
        assert rollback_event.trust_score_before == 2.5
        assert rollback_event.trust_score_after < rollback_event.trust_score_before
    
    def test_rollback_history_filtering(self):
        """Test rollback history filtering functionality."""
        # Generate rollbacks with different types and codes
        rollbacks = [
            ('instruction_limit', 'code1'),
            ('memory_limit', 'code2'),
            ('instruction_limit', 'code3'),
            ('arithmetic_overflow', 'code1')
        ]
        
        for violation_type, code_hash in rollbacks:
            self.rollback_handler.trigger_rollback(
                violation_type=violation_type,
                code_hash=code_hash,
                details=f'Test {violation_type}',
                context=ExecutionContext(),
                violations=[SecurityViolation(violation_type, 'Test')],
                trust_score_before=1.0
            )
        
        # Test filtering by violation type
        instruction_events = self.rollback_handler.get_rollback_history(
            violation_type='instruction_limit'
        )
        assert len(instruction_events) == 2
        for event in instruction_events:
            assert event.violation_type == 'instruction_limit'
        
        # Test filtering by code hash
        code1_events = self.rollback_handler.get_rollback_history(
            code_hash='code1'
        )
        assert len(code1_events) == 2
        for event in code1_events:
            assert event.code_hash == 'code1'
        
        # Test combined filtering
        combined_events = self.rollback_handler.get_rollback_history(
            code_hash='code1',
            violation_type='instruction_limit'
        )
        assert len(combined_events) == 1
        assert combined_events[0].code_hash == 'code1'
        assert combined_events[0].violation_type == 'instruction_limit'
    
    def test_rollback_configuration(self):
        """Test rollback configuration settings."""
        # Test disabling rollback
        self.rollback_handler.enable_rollback(False)
        assert self.rollback_handler.rollback_enabled == False
        
        # Attempt rollback when disabled
        rollback_event = self.rollback_handler.trigger_rollback(
            violation_type='instruction_limit',
            code_hash='test1234567890ab',
            details='Test violation',
            context=ExecutionContext(),
            violations=[SecurityViolation('instruction_limit', 'Test')],
            trust_score_before=2.0
        )
        
        # Should return None when disabled
        assert rollback_event is None
        assert len(self.rollback_handler.rollback_history) == 0
        
        # Re-enable rollback
        self.rollback_handler.enable_rollback(True)
        assert self.rollback_handler.rollback_enabled == True
        
        # Test auto trust revocation setting
        self.rollback_handler.set_auto_trust_revocation(False)
        assert self.rollback_handler.auto_trust_revocation == False
        
        self.rollback_handler.set_auto_trust_revocation(True)
        assert self.rollback_handler.auto_trust_revocation == True
    
    def test_rollback_history_management(self):
        """Test rollback history size management."""
        # Set small history limit
        self.rollback_handler.max_rollback_history = 3
        
        # Generate more rollbacks than limit
        for i in range(5):
            self.rollback_handler.trigger_rollback(
                violation_type='instruction_limit',
                code_hash=f'code{i}',
                details=f'Violation {i}',
                context=ExecutionContext(),
                violations=[SecurityViolation('instruction_limit', f'Test {i}')],
                trust_score_before=1.0
            )
        
        # Verify history size is limited
        assert len(self.rollback_handler.rollback_history) == 3
        
        # Verify most recent events are kept
        history = self.rollback_handler.rollback_history
        for i, event in enumerate(history):
            expected_index = 2 + i  # Should keep events 2, 3, 4
            assert event.details == f'Violation {expected_index}'
        
        # Test history cleanup
        cleared_count = self.rollback_handler.clear_rollback_history()
        assert cleared_count == 3
        assert len(self.rollback_handler.rollback_history) == 0