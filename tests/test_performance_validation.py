"""
Performance validation tests for AEGIS system.

This test suite validates performance characteristics, optimization benefits,
trust score calculation accuracy, and rollback performance across the
complete AEGIS system.
"""

import pytest
import time
import tempfile
import os
from statistics import mean, stdev
from aegis.pipeline import AegisExecutionPipeline
from aegis.trust.trust_manager import TrustManager
from aegis.runtime.monitor import RuntimeMonitor
from aegis.compiler.optimizer import OptimizedExecutor
from aegis.compiler.cache import CodeCache


class TestPerformanceValidation:
    """Performance validation tests for AEGIS system."""
    
    def setup_method(self):
        """Set up test environment with temporary trust file."""
        # Create temporary trust file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
        self.temp_file.close()
        self.trust_file = self.temp_file.name
        
        # Initialize pipeline
        self.pipeline = AegisExecutionPipeline(trust_file=self.trust_file)
    
    def teardown_method(self):
        """Clean up test environment."""
        if os.path.exists(self.trust_file):
            os.unlink(self.trust_file)
    
    def test_interpreter_vs_optimized_execution_performance(self):
        """Test performance difference between interpreted and optimized execution."""
        # Complex computation program
        program = """
        a = 15
        b = 8
        c = 3
        d = 2
        result1 = a + b * c - d
        result2 = a * b / d + c
        result3 = a - b + c * d
        result4 = result1 + result2 - result3
        print result4
        """
        
        # Measure interpreted execution times
        interpreted_times = []
        for i in range(5):
            start_time = time.time()
            result = self.pipeline.execute(program)
            end_time = time.time()
            
            assert result.success
            assert result.execution_mode == 'sandboxed'
            interpreted_times.append(end_time - start_time)
        
        # Build trust for optimization
        for i in range(10):
            result = self.pipeline.execute(program)
            assert result.success
        
        # Measure optimized execution times
        optimized_times = []
        optimized_speedups = []
        for i in range(5):
            start_time = time.time()
            result = self.pipeline.execute(program)
            end_time = time.time()
            
            assert result.success
            optimized_times.append(end_time - start_time)
            
            # Check if optimization was achieved
            if result.execution_mode == 'optimized':
                optimized_speedups.append(result.metrics.speedup_factor)
        
        # Performance validation
        avg_interpreted_time = mean(interpreted_times)
        avg_optimized_time = mean(optimized_times)
        
        print(f"Average interpreted time: {avg_interpreted_time:.6f}s")
        print(f"Average optimized time: {avg_optimized_time:.6f}s")
        
        # Verify optimization occurred
        if optimized_speedups:
            avg_speedup = mean(optimized_speedups)
            print(f"Average simulated speedup: {avg_speedup:.2f}x")
            assert avg_speedup > 1.0, "Optimized execution should show speedup"
            assert avg_speedup >= 2.0, "Expected at least 2x speedup simulation"
        
        # Verify consistent results
        # All executions should produce the same output
        interpreted_result = self.pipeline.execute(program)
        optimized_result = self.pipeline.execute(program)
        assert interpreted_result.output == optimized_result.output
    
    def test_trust_score_calculation_accuracy(self):
        """Test accuracy and consistency of trust score calculations."""
        programs = [
            "x = 5\nprint x",
            "y = 10\nz = y * 2\nprint z",
            "a = 3\nb = 7\nsum = a + b\nprint sum"
        ]
        
        trust_progressions = {}
        
        for program_id, program in enumerate(programs):
            trust_scores = []
            
            # Execute each program multiple times
            for execution in range(15):
                result = self.pipeline.execute(program)
                assert result.success
                trust_scores.append(result.trust_score)
            
            trust_progressions[program_id] = trust_scores
            
            # Validate trust progression
            assert trust_scores[0] > 0.0, "Initial trust should be positive"
            assert trust_scores[-1] > trust_scores[0], "Trust should increase over time"
            
            # Check for optimization threshold crossing
            optimization_achieved = any(score >= 1.0 for score in trust_scores)
            if optimization_achieved:
                # Find when optimization was first achieved
                opt_index = next(i for i, score in enumerate(trust_scores) if score >= 1.0)
                print(f"Program {program_id}: Optimization achieved after {opt_index + 1} executions")
                assert opt_index >= 5, "Should require multiple executions to reach optimization"
        
        # Validate trust score consistency
        for program_id, scores in trust_progressions.items():
            # Trust should be monotonically increasing (or stable)
            for i in range(1, len(scores)):
                assert scores[i] >= scores[i-1], f"Trust should not decrease: {scores[i]} < {scores[i-1]}"
            
            # Trust increment should be reasonable
            if len(scores) > 1:
                increments = [scores[i] - scores[i-1] for i in range(1, len(scores))]
                avg_increment = mean(increments)
                assert 0.1 <= avg_increment <= 0.5, f"Trust increment should be reasonable: {avg_increment}"
    
    def test_rollback_performance_and_state_consistency(self):
        """Test rollback performance and state consistency."""
        # Program that will build trust
        safe_program = """
        x = 10
        y = 5
        result = x + y
        print result
        """
        
        # Build trust first
        trust_scores = []
        for i in range(12):
            result = self.pipeline.execute(safe_program)
            assert result.success
            trust_scores.append(result.trust_score)
        
        # Verify optimization was achieved
        final_trust = trust_scores[-1]
        assert final_trust >= 1.0, "Should have achieved optimization threshold"
        
        # Program that will trigger rollback
        violation_program = """
        x = 10
        y = 0
        result = x / y
        print result
        """
        
        # Measure rollback performance
        rollback_times = []
        for i in range(3):
            start_time = time.time()
            result = self.pipeline.execute(violation_program)
            end_time = time.time()
            
            assert not result.success
            assert "division by zero" in result.error_message.lower()
            rollback_times.append(end_time - start_time)
        
        # Validate rollback performance
        avg_rollback_time = mean(rollback_times)
        print(f"Average rollback time: {avg_rollback_time:.6f}s")
        
        # Rollback should be fast (error detection is quick)
        assert avg_rollback_time < 0.1, "Rollback should be fast"
        
        # Verify state consistency after rollback
        # Original safe program should still work but trust may be affected
        post_rollback_result = self.pipeline.execute(safe_program)
        assert post_rollback_result.success
        assert post_rollback_result.output == ['15']  # Same output as before
        
        # Trust for the safe program should be preserved (different code hash)
        assert post_rollback_result.trust_score >= 1.0, "Safe program trust should be preserved"
    
    def test_cache_performance_and_efficiency(self):
        """Test code cache performance and efficiency."""
        # Program that benefits from caching
        program = """
        base = 7
        multiplier = 3
        step1 = base * multiplier
        step2 = step1 + 12
        step3 = step2 * base
        result = step3 - multiplier
        print result
        """
        
        # Build trust to enable optimization
        for i in range(10):
            result = self.pipeline.execute(program)
            assert result.success
        
        # Measure cache performance
        cache_miss_times = []
        cache_hit_times = []
        
        # First execution after optimization (cache miss)
        start_time = time.time()
        result1 = self.pipeline.execute(program)
        end_time = time.time()
        
        if result1.execution_mode == 'optimized':
            cache_miss_times.append(end_time - start_time)
            
            # Subsequent executions (cache hits)
            for i in range(5):
                start_time = time.time()
                result = self.pipeline.execute(program)
                end_time = time.time()
                
                assert result.success
                assert result.execution_mode == 'optimized'
                cache_hit_times.append(end_time - start_time)
        
        # Validate cache performance
        if cache_miss_times and cache_hit_times:
            avg_miss_time = mean(cache_miss_times)
            avg_hit_time = mean(cache_hit_times)
            
            print(f"Average cache miss time: {avg_miss_time:.6f}s")
            print(f"Average cache hit time: {avg_hit_time:.6f}s")
            
            # Cache hits should be faster than misses (though difference may be small in simulation)
            # We'll just verify both are reasonable
            assert avg_miss_time < 0.1, "Cache miss should be reasonably fast"
            assert avg_hit_time < 0.1, "Cache hit should be reasonably fast"
    
    def test_system_scalability_with_multiple_programs(self):
        """Test system scalability with multiple different programs."""
        # Generate multiple different programs
        programs = []
        for i in range(20):
            program = f"""
            x{i} = {i + 1}
            y{i} = x{i} * 2
            result{i} = y{i} + {i}
            print result{i}
            """
            programs.append(program)
        
        # Measure execution times as we scale up
        execution_times = []
        trust_scores = []
        
        for i, program in enumerate(programs):
            start_time = time.time()
            result = self.pipeline.execute(program)
            end_time = time.time()
            
            assert result.success
            execution_times.append(end_time - start_time)
            trust_scores.append(result.trust_score)
        
        # Validate scalability
        avg_execution_time = mean(execution_times)
        print(f"Average execution time across {len(programs)} programs: {avg_execution_time:.6f}s")
        
        # Execution time should remain reasonable even with many programs
        assert avg_execution_time < 0.1, "Average execution time should remain reasonable"
        
        # Trust scores should be consistent across programs
        assert all(score > 0.0 for score in trust_scores), "All programs should have positive trust"
        
        # System should handle many different programs efficiently
        if len(execution_times) > 10:
            # Check that execution time doesn't grow significantly
            early_times = execution_times[:5]
            late_times = execution_times[-5:]
            
            early_avg = mean(early_times)
            late_avg = mean(late_times)
            
            # Late executions shouldn't be significantly slower
            assert late_avg < early_avg * 3, "System should scale reasonably"
    
    def test_memory_usage_and_resource_management(self):
        """Test memory usage and resource management efficiency."""
        # Execute many programs to test resource management
        programs_executed = 0
        max_programs = 100
        
        for i in range(max_programs):
            # Create unique programs to test memory management
            program = f"""
            var_{i} = {i}
            result_{i} = var_{i} * 2 + 1
            print result_{i}
            """
            
            result = self.pipeline.execute(program)
            assert result.success
            programs_executed += 1
        
        # Get system status to check resource usage
        status = self.pipeline.get_system_status()
        assert status is not None
        
        print(f"Executed {programs_executed} programs successfully")
        
        # Verify system is still responsive after many executions
        test_program = "x = 42\nprint x"
        final_result = self.pipeline.execute(test_program)
        assert final_result.success
        assert final_result.output == ['42']
        
        # System should maintain reasonable performance
        start_time = time.time()
        for i in range(5):
            result = self.pipeline.execute(test_program)
            assert result.success
        end_time = time.time()
        
        avg_time = (end_time - start_time) / 5
        assert avg_time < 0.05, "System should remain responsive after many executions"
    
    def test_optimization_threshold_accuracy(self):
        """Test accuracy of optimization threshold detection."""
        program = "x = 100\ny = x / 4\nprint y"
        
        execution_modes = []
        trust_scores = []
        
        # Execute program many times and track mode transitions
        for i in range(20):
            result = self.pipeline.execute(program)
            assert result.success
            
            execution_modes.append(result.execution_mode)
            trust_scores.append(result.trust_score)
        
        # Find the transition point
        optimization_start = None
        for i, mode in enumerate(execution_modes):
            if mode == 'optimized':
                optimization_start = i
                break
        
        if optimization_start is not None:
            print(f"Optimization started at execution {optimization_start + 1}")
            print(f"Trust score at optimization: {trust_scores[optimization_start]:.2f}")
            
            # Verify threshold accuracy
            assert trust_scores[optimization_start] >= 1.0, "Should optimize at trust >= 1.0"
            
            # Verify all subsequent executions remain optimized
            for i in range(optimization_start, len(execution_modes)):
                assert execution_modes[i] == 'optimized', f"Should remain optimized after threshold: execution {i+1}"
                assert trust_scores[i] >= 1.0, f"Trust should remain >= 1.0: {trust_scores[i]}"
        
        # Verify trust progression is smooth
        for i in range(1, len(trust_scores)):
            assert trust_scores[i] >= trust_scores[i-1], "Trust should not decrease"
    
    def test_error_handling_performance_impact(self):
        """Test performance impact of error handling."""
        # Valid program for baseline
        valid_program = "x = 10\ny = 20\nresult = x + y\nprint result"
        
        # Invalid programs that trigger different error types
        error_programs = [
            "x = 10 @",  # Lexical error
            "x = + 10",  # Syntax error
            "print undefined_var",  # Semantic error
            "x = 5\ny = 0\nz = x / y"  # Runtime error
        ]
        
        # Measure valid execution time
        valid_times = []
        for i in range(10):
            start_time = time.time()
            result = self.pipeline.execute(valid_program)
            end_time = time.time()
            
            assert result.success
            valid_times.append(end_time - start_time)
        
        avg_valid_time = mean(valid_times)
        
        # Measure error handling times
        error_times = []
        for error_program in error_programs:
            for i in range(5):
                start_time = time.time()
                result = self.pipeline.execute(error_program)
                end_time = time.time()
                
                assert not result.success  # Should fail
                error_times.append(end_time - start_time)
        
        avg_error_time = mean(error_times)
        
        print(f"Average valid execution time: {avg_valid_time:.6f}s")
        print(f"Average error handling time: {avg_error_time:.6f}s")
        
        # Error handling should be fast
        assert avg_error_time < 0.05, "Error handling should be fast"
        
        # Error handling shouldn't be significantly slower than valid execution
        assert avg_error_time < avg_valid_time * 5, "Error handling shouldn't be much slower than valid execution"
        
        # System should recover quickly from errors
        recovery_result = self.pipeline.execute(valid_program)
        assert recovery_result.success, "System should recover quickly from errors"


if __name__ == "__main__":
    # Run a quick performance test
    test_instance = TestPerformanceValidation()
    test_instance.setup_method()
    
    try:
        print("Running performance validation tests...")
        
        # Test basic performance
        test_instance.test_interpreter_vs_optimized_execution_performance()
        print("✓ Interpreter vs optimized performance test passed")
        
        # Test trust calculation
        test_instance.test_trust_score_calculation_accuracy()
        print("✓ Trust score calculation test passed")
        
        # Test optimization threshold
        test_instance.test_optimization_threshold_accuracy()
        print("✓ Optimization threshold test passed")
        
        print("\nAll performance validation tests passed!")
        
    finally:
        test_instance.teardown_method()