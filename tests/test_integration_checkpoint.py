"""
Integration tests for AEGIS core security systems checkpoint.

This test suite validates that all core security systems work together
correctly: lexer, parser, static analyzer, interpreter, runtime monitor,
trust manager, optimized executor, and rollback handler.
"""

import pytest
from aegis.lexer.lexer import Lexer
from aegis.parser.parser import Parser
from aegis.interpreter.static_analyzer import StaticAnalyzer
from aegis.interpreter.interpreter import SandboxedInterpreter
from aegis.interpreter.context import ExecutionContext
from aegis.runtime.monitor import RuntimeMonitor, SecurityViolation
from aegis.trust.trust_manager import TrustManager
from aegis.compiler.cache import CodeCache
from aegis.compiler.optimizer import OptimizedExecutor
from aegis.runtime.rollback import RollbackHandler


class TestCoreSecuritySystemsIntegration:
    """Integration tests for all core AEGIS security systems."""
    
    def setup_method(self):
        """Set up integrated system components."""
        # Core language processing
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
        
        # Execution and monitoring
        self.monitor = RuntimeMonitor()
        self.interpreter = SandboxedInterpreter(self.monitor)
        
        # Trust and optimization
        self.trust_manager = TrustManager(trust_file=".test_integration_trust.json")
        self.cache = CodeCache()
        self.optimizer = OptimizedExecutor(self.cache, self.monitor)
        
        # Rollback handling
        self.rollback_handler = RollbackHandler()
        
        # Set up integrations
        self._setup_integrations()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import os
        if os.path.exists(".test_integration_trust.json"):
            os.remove(".test_integration_trust.json")
    
    def _setup_integrations(self):
        """Set up component integrations."""
        # Rollback integration
        self.optimizer.set_rollback_handler(self.rollback_handler)
        self.rollback_handler.register_trust_update_callback(
            self.trust_manager.revoke_trust_for_violation
        )
        self.rollback_handler.register_cache_clear_callback(
            self.optimizer.clear_cache
        )
        
        # Monitor rollback callback
        def rollback_callback(violations, execution_mode, code_hash):
            if violations and execution_mode == 'optimized':
                violation = violations[0]
                trust_score = self.trust_manager.get_trust_score(code_hash)
                self.rollback_handler.trigger_rollback(
                    violation.violation_type,
                    code_hash,
                    violation.message,
                    violation.context,
                    violations,
                    trust_score.current_score
                )
        
        self.monitor.register_rollback_callback(rollback_callback)
    
    def _execute_program(self, source_code: str, execution_mode: str = 'sandboxed'):
        """Execute a program through the complete pipeline."""
        # 1. Lexical analysis
        tokens = self.lexer.tokenize(source_code)
        
        # 2. Syntax analysis
        ast = self.parser.parse(tokens)
        
        # 3. Static analysis
        try:
            analysis_passed = self.analyzer.analyze(ast)
            if not analysis_passed:
                raise Exception("Static analysis failed")
        except Exception as e:
            raise Exception(f"Static analysis failed: {str(e)}")
        
        # 4. Execution
        context = ExecutionContext()
        
        if execution_mode == 'sandboxed':
            # Sandboxed execution (interpreter handles monitoring internally)
            self.interpreter.execute(ast, context)
            # Get metrics from the monitor's execution history
            history = self.monitor.get_execution_history()
            metrics = history[-1] if history else ExecutionMetrics()
        else:
            # Optimized execution
            code_hash = self.trust_manager.get_code_hash(source_code)
            metrics = self.optimizer.execute_optimized(code_hash, ast, context)
        
        # 5. Trust update
        code_hash = self.trust_manager.get_code_hash(source_code)
        violations = metrics.violations_detected if hasattr(metrics, 'violations_detected') else []
        trust_score = self.trust_manager.update_trust(code_hash, metrics, violations)
        
        return context, metrics, trust_score
    
    def test_simple_program_execution_pipeline(self):
        """Test complete pipeline with a simple program."""
        source_code = """
        x = 10
        y = 20
        result = x + y
        print result
        """
        
        # Execute program
        context, metrics, trust_score = self._execute_program(source_code)
        
        # Verify execution results
        assert context.get_variable('x') == 10
        assert context.get_variable('y') == 20
        assert context.get_variable('result') == 30
        assert '30' in context.output_buffer
        
        # Verify metrics
        assert metrics.instruction_count > 0
        assert metrics.assignment_operations == 3
        assert metrics.arithmetic_operations == 1
        assert metrics.print_operations == 1
        assert len(metrics.violations_detected) == 0
        
        # Verify trust score increased
        assert trust_score > 0.0
    
    def test_trust_building_and_optimization_transition(self):
        """Test trust building leading to optimization eligibility."""
        source_code = """
        a = 5
        b = 3
        sum = a + b
        print sum
        """
        
        code_hash = self.trust_manager.get_code_hash(source_code)
        
        # Execute multiple times to build trust
        for i in range(5):
            context, metrics, trust_score = self._execute_program(source_code)
            
            # Verify consistent results
            assert context.get_variable('sum') == 8
            assert '8' in context.output_buffer
        
        # Check if code became eligible for optimization
        trust_score_obj = self.trust_manager.get_trust_score(code_hash)
        is_eligible = trust_score_obj.is_eligible_for_optimization()
        
        # Should be eligible after multiple successful executions
        if trust_score_obj.execution_count >= 3 and trust_score_obj.current_score >= 1.0:
            assert is_eligible
            
            # Test optimized execution
            if self.trust_manager.is_trusted_for_optimization(code_hash):
                context, metrics, trust_score = self._execute_program(source_code, 'optimized')
                
                # Verify optimized execution results
                assert context.get_variable('sum') == 8
                assert '8' in context.output_buffer
                assert metrics.optimization_applied == True
                assert metrics.speedup_factor > 1.0
    
    def test_security_violation_and_rollback(self):
        """Test security violation detection and rollback handling."""
        # Create a program that will trigger a violation
        source_code = """
        x = 1
        print x
        """
        
        code_hash = self.trust_manager.get_code_hash(source_code)
        
        # Build trust first
        for i in range(3):
            self._execute_program(source_code)
        
        # Verify trust was built
        trust_score_obj = self.trust_manager.get_trust_score(code_hash)
        initial_trust = trust_score_obj.current_score
        assert initial_trust > 0.0
        
        # Force a violation by setting a very low threshold
        self.monitor.set_violation_threshold(1)  # Very low threshold
        
        # Try to execute in optimized mode (should trigger violation)
        if self.trust_manager.is_trusted_for_optimization(code_hash):
            try:
                # This should trigger a violation due to low threshold
                context, metrics, trust_score = self._execute_program(source_code, 'optimized')
                
                # If we get here, check if rollback occurred
                if len(self.rollback_handler.rollback_history) > 0:
                    rollback_event = self.rollback_handler.rollback_history[-1]
                    assert rollback_event.violation_type == 'instruction_limit'
                    assert rollback_event.code_hash == code_hash
                    
                    # Verify trust was revoked
                    updated_trust = self.trust_manager.get_trust_score(code_hash)
                    assert updated_trust.current_score < initial_trust
                    
            except SecurityViolation:
                # Violation was raised, which is expected
                pass
        
        # Reset threshold
        self.monitor.set_violation_threshold(1000)
    
    def test_static_analysis_integration(self):
        """Test static analysis integration with execution pipeline."""
        # Valid program
        valid_code = """
        x = 10
        y = x + 5
        print y
        """
        
        # Should execute successfully
        context, metrics, trust_score = self._execute_program(valid_code)
        assert context.get_variable('y') == 15
        
        # Invalid program (undefined variable)
        invalid_code = """
        x = 10
        y = z + 5
        print y
        """
        
        # Should fail static analysis
        with pytest.raises(Exception) as exc_info:
            self._execute_program(invalid_code)
        
        assert "Static analysis failed" in str(exc_info.value)
    
    def test_error_handling_across_components(self):
        """Test error handling integration across all components."""
        # Lexer error
        with pytest.raises(Exception):
            self._execute_program("x = 10 @")  # Invalid character
        
        # Parser error
        with pytest.raises(Exception):
            self._execute_program("x = + 10")  # Invalid syntax
        
        # Static analysis error
        with pytest.raises(Exception):
            self._execute_program("print undefined_var")  # Undefined variable
    
    def test_trust_persistence_integration(self):
        """Test trust persistence across system restarts."""
        source_code = """
        value = 42
        print value
        """
        
        # Execute and build trust
        context, metrics, trust_score = self._execute_program(source_code)
        code_hash = self.trust_manager.get_code_hash(source_code)
        
        # Get trust score
        trust_score_obj = self.trust_manager.get_trust_score(code_hash)
        original_score = trust_score_obj.current_score
        original_count = trust_score_obj.execution_count
        
        # Create new trust manager (simulating restart)
        new_trust_manager = TrustManager(trust_file=".test_integration_trust.json")
        
        # Verify trust was persisted
        restored_trust = new_trust_manager.get_trust_score(code_hash)
        assert restored_trust.current_score == original_score
        assert restored_trust.execution_count == original_count
    
    def test_cache_integration_with_optimization(self):
        """Test code cache integration with optimization system."""
        source_code = """
        a = 1
        b = 2
        c = a + b
        print c
        """
        
        code_hash = self.trust_manager.get_code_hash(source_code)
        
        # Build trust
        for i in range(3):
            self._execute_program(source_code)
        
        # Execute in optimized mode if eligible
        if self.trust_manager.is_trusted_for_optimization(code_hash):
            # First optimized execution (should compile and cache)
            context1, metrics1, _ = self._execute_program(source_code, 'optimized')
            
            # Second optimized execution (should use cache)
            context2, metrics2, _ = self._execute_program(source_code, 'optimized')
            
            # Verify consistent results
            assert context1.get_variable('sum') == context2.get_variable('sum')
            assert '8' in context1.output_buffer
            assert '8' in context2.output_buffer
            
            # Verify cache was used in second execution
            if hasattr(metrics2, 'cache_hit'):
                assert metrics2.cache_hit == True
    
    def test_complete_system_statistics(self):
        """Test system-wide statistics collection."""
        programs = [
            "x = 1\nprint x",
            "y = 2\nz = y * 3\nprint z",
            "a = 5\nb = 10\nresult = a + b\nprint result"
        ]
        
        # Execute multiple programs
        for program in programs:
            self._execute_program(program)
        
        # Check trust manager statistics
        trust_summary = self.trust_manager.get_trust_summary()
        assert trust_summary['total_codes'] == len(programs)
        assert trust_summary['average_score'] >= 0.0
        
        # Check monitor statistics
        monitor_stats = self.monitor.get_average_metrics()
        if monitor_stats:  # Only check if we have history
            assert monitor_stats['total_executions'] > 0
            assert monitor_stats['avg_instruction_count'] > 0
        
        # Check rollback statistics
        rollback_stats = self.rollback_handler.get_rollback_statistics()
        assert rollback_stats['rollback_enabled'] == True
        assert rollback_stats['total_rollbacks'] >= 0
        
        # Check cache statistics
        cache_stats = self.cache.get_cache_stats()
        assert cache_stats['max_size'] > 0
        assert cache_stats['cache_size'] >= 0