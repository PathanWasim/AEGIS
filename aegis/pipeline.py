"""
Main execution pipeline for AEGIS.

This module provides the primary interface for executing AEGIS programs
with the complete security model: adaptive execution, trust management,
monitoring, and rollback handling.
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .lexer.lexer import Lexer
from .parser.parser import Parser
from .interpreter.static_analyzer import StaticAnalyzer
from .interpreter.interpreter import SandboxedInterpreter
from .errors import LexicalError, SyntaxError as AegisSyntaxError, SemanticError, RuntimeError as AegisRuntimeError
from .interpreter.context import ExecutionContext, ExecutionMode
from .runtime.monitor import RuntimeMonitor, SecurityViolation, ExecutionMetrics
from .trust.trust_manager import TrustManager
from .compiler.cache import CodeCache
from .compiler.optimizer import OptimizedExecutor
from .runtime.rollback import RollbackHandler, RollbackEvent


@dataclass
class ExecutionResult:
    """
    Result of program execution through the AEGIS pipeline.
    
    Contains execution output, metrics, trust information, and any
    security events that occurred during execution.
    """
    success: bool
    output: List[str]
    execution_time: float
    execution_mode: str  # 'sandboxed' or 'optimized'
    trust_score: float
    trust_level: str
    metrics: ExecutionMetrics
    violations: List[SecurityViolation]
    rollback_events: List[RollbackEvent]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'success': self.success,
            'output': self.output,
            'execution_time': self.execution_time,
            'execution_mode': self.execution_mode,
            'trust_score': self.trust_score,
            'trust_level': self.trust_level,
            'metrics': self.metrics.to_dict(),
            'violations': [str(v) for v in self.violations],
            'rollback_events': [event.to_dict() for event in self.rollback_events],
            'error_message': self.error_message
        }


class AegisExecutionPipeline:
    """
    Main execution pipeline for AEGIS programs.
    
    This pipeline orchestrates the complete AEGIS execution model:
    1. Lexical analysis (tokenization)
    2. Syntax analysis (parsing)
    3. Static security analysis
    4. Execution mode determination (trust-based)
    5. Program execution (sandboxed or optimized)
    6. Runtime monitoring and violation detection
    7. Trust score updates
    8. Rollback handling for security violations
    
    The pipeline provides adaptive security through trust-based execution
    mode selection and automatic rollback on security violations.
    """
    
    def __init__(self, 
                 trust_file: str = ".aegis_trust.json",
                 cache_size: int = 100,
                 violation_threshold: int = 1000,
                 trust_threshold: float = 1.0):
        """
        Initialize the AEGIS execution pipeline.
        
        Args:
            trust_file: File path for trust data persistence
            cache_size: Maximum size of optimization cache
            violation_threshold: Instruction count limit for violation detection
            trust_threshold: Minimum trust score for optimization
        """
        # Core language processing components
        self.lexer = Lexer()
        self.parser = Parser()
        self.analyzer = StaticAnalyzer()
        
        # Execution and monitoring components
        self.monitor = RuntimeMonitor()
        self.interpreter = SandboxedInterpreter(self.monitor)
        
        # Trust and optimization components
        self.trust_manager = TrustManager(trust_file=trust_file)
        self.cache = CodeCache(max_size=cache_size)
        self.optimizer = OptimizedExecutor(self.cache, self.monitor)
        
        # Rollback handling
        self.rollback_handler = RollbackHandler()
        
        # Configuration
        self.violation_threshold = violation_threshold
        self.trust_threshold = trust_threshold
        
        # Setup integrations
        self._setup_integrations()
        
        # Execution statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.optimized_executions = 0
        self.rollback_count = 0
    
    def _setup_integrations(self):
        """Set up component integrations and callbacks."""
        # Configure trust threshold
        self.trust_manager.set_trust_threshold(self.trust_threshold)
        
        # Configure violation threshold
        self.monitor.set_violation_threshold(self.violation_threshold)
        
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
                rollback_event = self.rollback_handler.trigger_rollback(
                    violation.violation_type,
                    code_hash,
                    violation.message,
                    violation.context,
                    violations,
                    trust_score.current_score
                )
                self.rollback_count += 1
                return rollback_event
            return None
        
        self.monitor.register_rollback_callback(rollback_callback)
    
    def execute(self, source_code: str, verbose: bool = True) -> ExecutionResult:
        """
        Execute AEGIS program through the complete pipeline.
        
        Args:
            source_code: The AEGIS source code to execute
            verbose: Whether to print execution information
            
        Returns:
            ExecutionResult with execution details and metrics
        """
        start_time = time.time()
        self.total_executions += 1
        
        if verbose:
            print(f"\n[AEGIS] Starting execution #{self.total_executions}")
            print(f"[AEGIS] Source code ({len(source_code)} chars)")
        
        try:
            # 1. Lexical Analysis
            if verbose:
                print("[AEGIS] Phase 1: Lexical analysis...")
            tokens = self.lexer.tokenize(source_code)
            
            # 2. Syntax Analysis
            if verbose:
                print("[AEGIS] Phase 2: Syntax analysis...")
            ast = self.parser.parse(tokens)
            
            # 3. Static Security Analysis
            if verbose:
                print("[AEGIS] Phase 3: Static security analysis...")
            analysis_passed = self.analyzer.analyze(ast)
            if not analysis_passed:
                raise AnalysisError("Static analysis failed")
            
            # 4. Execution Mode Determination
            code_hash = self.trust_manager.get_code_hash(source_code)
            trust_score_obj = self.trust_manager.get_trust_score(code_hash)
            is_trusted = self.trust_manager.is_trusted_for_optimization(code_hash)
            
            execution_mode = 'optimized' if is_trusted else 'sandboxed'
            
            if verbose:
                print(f"[AEGIS] Phase 4: Execution mode determination...")
                print(f"[AEGIS] Trust score: {trust_score_obj.current_score:.2f} ({trust_score_obj.get_trust_level()})")
                print(f"[AEGIS] Execution mode: {execution_mode.upper()}")
            
            # 5. Program Execution
            if verbose:
                print(f"[AEGIS] Phase 5: Program execution ({execution_mode})...")
            
            context = ExecutionContext()
            violations = []
            rollback_events = []
            
            try:
                if execution_mode == 'sandboxed':
                    # Sandboxed execution
                    self.interpreter.execute(ast, context)
                    # Get metrics from monitor history
                    history = self.monitor.get_execution_history()
                    metrics = history[-1] if history else ExecutionMetrics()
                else:
                    # Optimized execution
                    self.optimized_executions += 1
                    metrics = self.optimizer.execute_optimized(code_hash, ast, context)
                
            except SecurityViolation as e:
                # Security violation occurred
                violations.append(e)
                if verbose:
                    print(f"[AEGIS] Security violation: {e.violation_type}")
                
                # Get rollback events
                rollback_events = self.rollback_handler.get_rollback_history(code_hash)
                
                # Get metrics (may be partial)
                history = self.monitor.get_execution_history()
                metrics = history[-1] if history else ExecutionMetrics()
                metrics.violations_detected.extend(violations)
            
            # 6. Trust Score Update
            if verbose:
                print("[AEGIS] Phase 6: Trust score update...")
            
            trust_score = self.trust_manager.update_trust(
                code_hash, metrics, violations
            )
            
            # 7. Execution Complete
            execution_time = time.time() - start_time
            self.successful_executions += 1
            
            if verbose:
                print(f"[AEGIS] Execution completed successfully in {execution_time:.3f}s")
                print(f"[AEGIS] Output: {context.output_buffer}")
            
            return ExecutionResult(
                success=True,
                output=context.output_buffer,
                execution_time=execution_time,
                execution_mode=execution_mode,
                trust_score=trust_score,
                trust_level=trust_score_obj.get_trust_level(),
                metrics=metrics,
                violations=violations,
                rollback_events=rollback_events
            )
            
        except (LexicalError, AegisSyntaxError, SemanticError, AegisRuntimeError) as e:
            # Execution failed - enhance error with source code context
            execution_time = time.time() - start_time
            
            # Add source code context to error if not already present
            if hasattr(e, 'context') and e.context and not e.context.source_code:
                e.context.source_code = source_code
            
            error_message = str(e)
            
            if verbose:
                print(f"[AEGIS] Execution failed:")
                print(f"[ERROR] {error_message}")
            
            return ExecutionResult(
                success=False,
                output=[],
                execution_time=execution_time,
                execution_mode='failed',
                trust_score=0.0,
                trust_level='NONE',
                metrics=ExecutionMetrics(),
                violations=[],
                rollback_events=[],
                error_message=error_message
            )
    
    def execute_batch(self, programs: List[str], verbose: bool = False) -> List[ExecutionResult]:
        """
        Execute multiple programs in batch.
        
        Args:
            programs: List of source code strings to execute
            verbose: Whether to print execution information
            
        Returns:
            List of ExecutionResult objects
        """
        results = []
        
        print(f"\n[AEGIS] Starting batch execution of {len(programs)} programs")
        
        for i, program in enumerate(programs):
            if verbose:
                print(f"\n[AEGIS] === Program {i+1}/{len(programs)} ===")
            
            result = self.execute(program, verbose=verbose)
            results.append(result)
            
            if not verbose:
                status = "✓" if result.success else "✗"
                mode = result.execution_mode[:4].upper()
                print(f"[AEGIS] Program {i+1}: {status} {mode} ({result.execution_time:.3f}s)")
        
        # Print batch summary
        successful = sum(1 for r in results if r.success)
        optimized = sum(1 for r in results if r.execution_mode == 'optimized')
        
        print(f"\n[AEGIS] Batch execution complete:")
        print(f"[AEGIS] Success rate: {successful}/{len(programs)} ({successful/len(programs)*100:.1f}%)")
        optimization_rate = optimized/successful*100 if successful > 0 else 0
        print(f"[AEGIS] Optimized executions: {optimized}/{successful} ({optimization_rate:.1f}%)")
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status and statistics.
        
        Returns:
            Dictionary with system status information
        """
        trust_summary = self.trust_manager.get_trust_summary()
        monitor_stats = self.monitor.get_average_metrics()
        rollback_stats = self.rollback_handler.get_rollback_statistics()
        cache_stats = self.cache.get_cache_stats()
        
        return {
            'execution_stats': {
                'total_executions': self.total_executions,
                'successful_executions': self.successful_executions,
                'optimized_executions': self.optimized_executions,
                'rollback_count': self.rollback_count,
                'success_rate': self.successful_executions / self.total_executions if self.total_executions > 0 else 0.0,
                'optimization_rate': self.optimized_executions / self.successful_executions if self.successful_executions > 0 else 0.0
            },
            'trust_system': trust_summary,
            'monitoring': monitor_stats,
            'rollback_system': rollback_stats,
            'cache_system': cache_stats,
            'configuration': {
                'violation_threshold': self.violation_threshold,
                'trust_threshold': self.trust_threshold,
                'cache_size': self.cache.max_size,
                'trust_file': self.trust_manager.trust_file
            }
        }
    
    def configure_system(self, 
                        violation_threshold: Optional[int] = None,
                        trust_threshold: Optional[float] = None,
                        optimization_enabled: Optional[bool] = None,
                        rollback_enabled: Optional[bool] = None) -> None:
        """
        Configure system parameters.
        
        Args:
            violation_threshold: Instruction count limit for violations
            trust_threshold: Minimum trust score for optimization
            optimization_enabled: Whether to enable trust-based optimization
            rollback_enabled: Whether to enable rollback functionality
        """
        if violation_threshold is not None:
            self.violation_threshold = violation_threshold
            self.monitor.set_violation_threshold(violation_threshold)
            print(f"[AEGIS] Violation threshold set to {violation_threshold}")
        
        if trust_threshold is not None:
            self.trust_threshold = trust_threshold
            self.trust_manager.set_trust_threshold(trust_threshold)
            print(f"[AEGIS] Trust threshold set to {trust_threshold}")
        
        if optimization_enabled is not None:
            self.trust_manager.enable_optimization(optimization_enabled)
            print(f"[AEGIS] Optimization {'enabled' if optimization_enabled else 'disabled'}")
        
        if rollback_enabled is not None:
            self.rollback_handler.enable_rollback(rollback_enabled)
            print(f"[AEGIS] Rollback {'enabled' if rollback_enabled else 'disabled'}")
    
    def cleanup_system(self) -> None:
        """Clean up system resources and temporary data."""
        # Clean up old trust data
        self.trust_manager.cleanup_old_trust_data()
        
        # Clean up expired cache entries
        expired_count = self.cache.cleanup_expired()
        if expired_count > 0:
            print(f"[AEGIS] Cleaned up {expired_count} expired cache entries")
        
        # Clear old rollback history
        cleared_count = self.rollback_handler.clear_rollback_history(older_than_days=7)
        if cleared_count > 0:
            print(f"[AEGIS] Cleaned up {cleared_count} old rollback events")
        
        print("[AEGIS] System cleanup completed")