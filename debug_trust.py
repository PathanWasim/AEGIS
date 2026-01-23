#!/usr/bin/env python3
"""Debug script to understand trust eligibility logic."""

from aegis.pipeline import AegisExecutionPipeline
import tempfile
import os

# Create temporary trust file
temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.json')
temp_file.close()
temp_trust_file = temp_file.name

try:
    pipeline = AegisExecutionPipeline(
        trust_file=temp_trust_file,
        trust_threshold=1.0,
        violation_threshold=1000
    )
    
    program = "x = 5\nprint x"
    
    print("Executing program multiple times to debug trust logic...")
    
    for i in range(10):
        result = pipeline.execute(program, verbose=False)
        
        # Get trust details
        code_hash = pipeline.trust_manager.get_code_hash(program)
        trust_score_obj = pipeline.trust_manager.get_trust_score(code_hash)
        is_trusted = pipeline.trust_manager.is_trusted_for_optimization(code_hash)
        
        print(f"\nExecution {i+1}:")
        print(f"  Success: {result.success}")
        print(f"  Trust Score: {result.trust_score:.2f}")
        print(f"  Execution Mode: {result.execution_mode}")
        print(f"  Execution Count: {trust_score_obj.execution_count}")
        print(f"  Successful Executions: {trust_score_obj.successful_executions}")
        print(f"  Success Rate: {trust_score_obj.successful_executions / trust_score_obj.execution_count:.2f}")
        print(f"  Is Trusted: {is_trusted}")
        print(f"  Optimization Enabled: {pipeline.trust_manager.optimization_enabled}")
        print(f"  Trust Threshold: {pipeline.trust_manager.trust_threshold}")
        
        # Check individual conditions
        meets_score = trust_score_obj.current_score >= pipeline.trust_manager.trust_threshold
        meets_count = trust_score_obj.execution_count >= 3
        meets_success_rate = trust_score_obj.successful_executions / trust_score_obj.execution_count >= 0.8
        
        print(f"  Meets Score Threshold: {meets_score} ({trust_score_obj.current_score:.2f} >= {pipeline.trust_manager.trust_threshold})")
        print(f"  Meets Execution Count: {meets_count} ({trust_score_obj.execution_count} >= 3)")
        print(f"  Meets Success Rate: {meets_success_rate} ({trust_score_obj.successful_executions / trust_score_obj.execution_count:.2f} >= 0.8)")
        
        if result.execution_mode == 'optimized':
            print("  *** OPTIMIZED MODE ACHIEVED ***")
            break

finally:
    # Clean up
    if os.path.exists(temp_trust_file):
        os.unlink(temp_trust_file)