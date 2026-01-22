"""
Rollback handling implementation for AEGIS.

This module manages transitions from optimized execution back to sandboxed
interpretation when security violations are detected, ensuring system safety
and maintaining execution state consistency.
"""

import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
from ..interpreter.context import ExecutionContext
from ..runtime.monitor import SecurityViolation, ExecutionMetrics
from ..ast.nodes import ASTNode


@dataclass
class RollbackEvent:
    """
    Represents a rollback occurrence with comprehensive details.
    
    This class captures all relevant information about a rollback event
    for analysis, logging, and trust management decisions.
    """
    timestamp: datetime
    violation_type: str
    code_hash: str
    details: str
    execution_mode: str  # 'optimized' or 'sandboxed'
    rollback_time: float  # Time taken to perform rollback
    context_state: Dict[str, Any]  # Execution context at rollback
    violation_count: int  # Number of violations that triggered rollback
    trust_score_before: float
    trust_score_after: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'timestamp': self.timestamp.isoformat(),
            'violation_type': self.violation_type,
            'code_hash': self.code_hash,
            'details': self.details,
            'execution_mode': self.execution_mode,
            'rollback_time': self.rollback_time,
            'context_state': self.context_state,
            'violation_count': self.violation_count,
            'trust_score_before': self.trust_score_before,
            'trust_score_after': self.trust_score_after
        }


class RollbackHandler:
    """
    Rollback handler for AEGIS security violations.
    
    This handler manages transitions from optimized execution back to sandboxed
    interpretation when security violations are detected. It ensures system
    safety by clearing caches, restoring execution state, and coordinating
    with trust management systems.
    
    Key responsibilities:
    - Detect rollback triggers from security violations
    - Clear optimization caches for compromised code
    - Restore execution state to safe sandboxed mode
    - Log rollback events for analysis and trust updates
    - Coordinate with trust manager for score adjustments
    """
    
    def __init__(self):
        """Initialize the rollback handler."""
        self.rollback_history: List[RollbackEvent] = []
        self.rollback_callbacks: List[Callable[[RollbackEvent], None]] = []
        self.cache_clear_callback: Optional[Callable[[str], None]] = None
        self.trust_update_callback: Optional[Callable[[str, str, str], None]] = None
        
        # Rollback configuration
        self.max_rollback_history = 100
        self.rollback_enabled = True
        self.auto_trust_revocation = True
        
        # Statistics
        self.total_rollbacks = 0
        self.rollbacks_by_type: Dict[str, int] = {}
        self.rollbacks_by_code: Dict[str, int] = {}
    
    def register_cache_clear_callback(self, callback: Callable[[str], None]) -> None:
        """
        Register callback for clearing optimization cache.
        
        Args:
            callback: Function to call for cache clearing (takes code_hash)
        """
        self.cache_clear_callback = callback
    
    def register_trust_update_callback(self, callback: Callable[[str, str, str], None]) -> None:
        """
        Register callback for updating trust scores.
        
        Args:
            callback: Function to call for trust updates (code_hash, violation_type, details)
        """
        self.trust_update_callback = callback
    
    def register_rollback_callback(self, callback: Callable[[RollbackEvent], None]) -> None:
        """
        Register callback to be notified of rollback events.
        
        Args:
            callback: Function to call when rollback occurs
        """
        self.rollback_callbacks.append(callback)
    
    def trigger_rollback(self, violation_type: str, code_hash: str, details: str,
                        context: ExecutionContext = None, 
                        violations: List[SecurityViolation] = None,
                        trust_score_before: float = 0.0) -> RollbackEvent:
        """
        Trigger rollback due to security violation.
        
        Args:
            violation_type: Type of security violation
            code_hash: Hash of the code that caused violation
            details: Detailed description of the violation
            context: Current execution context
            violations: List of security violations
            trust_score_before: Trust score before rollback
            
        Returns:
            RollbackEvent describing the rollback
        """
        if not self.rollback_enabled:
            print(f"[ROLLBACK] Rollback disabled - ignoring violation: {violation_type}")
            return None
        
        rollback_start = time.time()
        
        print(f"[ROLLBACK] Security violation detected: {violation_type}")
        print(f"[ROLLBACK] Code: {code_hash[:8]}... - {details}")
        print(f"[ROLLBACK] Initiating rollback to sandboxed execution...")
        
        # Clear optimization cache for the compromised code
        if self.cache_clear_callback:
            self.cache_clear_callback(code_hash)
            print(f"[ROLLBACK] Cleared optimization cache for code {code_hash[:8]}...")
        
        # Capture context state
        context_state = {}
        if context:
            context_state = {
                'variables': dict(context.variables),
                'variable_count': len(context.variables),
                'output_buffer': getattr(context, 'output_buffer', [])
            }
        
        # Update trust score
        trust_score_after = trust_score_before
        if self.trust_update_callback and self.auto_trust_revocation:
            self.trust_update_callback(code_hash, violation_type, details)
            # Assume trust score is significantly reduced after violation
            trust_score_after = max(0.0, trust_score_before - 0.5)
        
        rollback_time = time.time() - rollback_start
        
        # Create rollback event
        rollback_event = RollbackEvent(
            timestamp=datetime.now(),
            violation_type=violation_type,
            code_hash=code_hash,
            details=details,
            execution_mode='optimized',  # We're rolling back from optimized mode
            rollback_time=rollback_time,
            context_state=context_state,
            violation_count=len(violations) if violations else 1,
            trust_score_before=trust_score_before,
            trust_score_after=trust_score_after
        )
        
        # Record rollback
        self._record_rollback(rollback_event)
        
        # Notify callbacks
        for callback in self.rollback_callbacks:
            try:
                callback(rollback_event)
            except Exception as e:
                print(f"[ROLLBACK] Warning: Callback failed - {e}")
        
        print(f"[ROLLBACK] Rollback completed in {rollback_time:.3f}s")
        print(f"[ROLLBACK] Code {code_hash[:8]}... will execute in sandboxed mode")
        
        return rollback_event
    
    def should_rollback(self, violations: List[SecurityViolation], 
                       execution_mode: str = 'optimized') -> bool:
        """
        Determine if rollback should be triggered based on violations.
        
        Args:
            violations: List of detected security violations
            execution_mode: Current execution mode
            
        Returns:
            True if rollback should be triggered
        """
        if not self.rollback_enabled:
            return False
        
        # Only rollback if we're in optimized mode
        if execution_mode != 'optimized':
            return False
        
        # Rollback on any security violation in optimized mode
        if violations and len(violations) > 0:
            return True
        
        return False
    
    def restore_execution_state(self, context: ExecutionContext, 
                              safe_state: Dict[str, Any] = None) -> None:
        """
        Restore execution context to a safe state.
        
        Args:
            context: Execution context to restore
            safe_state: Safe state to restore to (optional)
        """
        if safe_state:
            # Restore from provided safe state
            if 'variables' in safe_state:
                context.variables = safe_state['variables'].copy()
            
            print(f"[ROLLBACK] Restored execution state from checkpoint")
        else:
            # Reset to clean state
            context.variables.clear()
            if hasattr(context, 'output_buffer'):
                context.output_buffer.clear()
            
            print(f"[ROLLBACK] Reset execution state to clean state")
    
    def get_rollback_history(self, code_hash: str = None, 
                           violation_type: str = None) -> List[RollbackEvent]:
        """
        Get rollback history with optional filtering.
        
        Args:
            code_hash: Filter by specific code hash
            violation_type: Filter by violation type
            
        Returns:
            List of matching rollback events
        """
        history = self.rollback_history
        
        if code_hash:
            history = [event for event in history if event.code_hash == code_hash]
        
        if violation_type:
            history = [event for event in history if event.violation_type == violation_type]
        
        return history
    
    def get_rollback_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive rollback statistics.
        
        Returns:
            Dictionary with rollback statistics
        """
        recent_rollbacks = len([
            event for event in self.rollback_history
            if (datetime.now() - event.timestamp).days < 7
        ])
        
        avg_rollback_time = 0.0
        if self.rollback_history:
            avg_rollback_time = sum(event.rollback_time for event in self.rollback_history) / len(self.rollback_history)
        
        return {
            'total_rollbacks': self.total_rollbacks,
            'recent_rollbacks': recent_rollbacks,
            'rollbacks_by_type': dict(self.rollbacks_by_type),
            'rollbacks_by_code': dict(self.rollbacks_by_code),
            'average_rollback_time': avg_rollback_time,
            'rollback_enabled': self.rollback_enabled,
            'auto_trust_revocation': self.auto_trust_revocation,
            'history_size': len(self.rollback_history)
        }
    
    def clear_rollback_history(self, older_than_days: int = None) -> int:
        """
        Clear rollback history.
        
        Args:
            older_than_days: Only clear events older than this many days
            
        Returns:
            Number of events cleared
        """
        if older_than_days is None:
            # Clear all history
            cleared_count = len(self.rollback_history)
            self.rollback_history.clear()
        else:
            # Clear old events
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            original_count = len(self.rollback_history)
            self.rollback_history = [
                event for event in self.rollback_history
                if event.timestamp > cutoff_date
            ]
            cleared_count = original_count - len(self.rollback_history)
        
        print(f"[ROLLBACK] Cleared {cleared_count} rollback events from history")
        return cleared_count
    
    def enable_rollback(self, enabled: bool = True) -> None:
        """
        Enable or disable rollback functionality.
        
        Args:
            enabled: Whether to enable rollback
        """
        self.rollback_enabled = enabled
        status = "enabled" if enabled else "disabled"
        print(f"[ROLLBACK] Rollback functionality {status}")
    
    def set_auto_trust_revocation(self, enabled: bool = True) -> None:
        """
        Enable or disable automatic trust revocation on rollback.
        
        Args:
            enabled: Whether to automatically revoke trust on rollback
        """
        self.auto_trust_revocation = enabled
        status = "enabled" if enabled else "disabled"
        print(f"[ROLLBACK] Automatic trust revocation {status}")
    
    def _record_rollback(self, event: RollbackEvent) -> None:
        """
        Record a rollback event in history and update statistics.
        
        Args:
            event: RollbackEvent to record
        """
        # Add to history
        self.rollback_history.append(event)
        
        # Maintain history size limit
        if len(self.rollback_history) > self.max_rollback_history:
            self.rollback_history = self.rollback_history[-self.max_rollback_history:]
        
        # Update statistics
        self.total_rollbacks += 1
        
        if event.violation_type in self.rollbacks_by_type:
            self.rollbacks_by_type[event.violation_type] += 1
        else:
            self.rollbacks_by_type[event.violation_type] = 1
        
        if event.code_hash in self.rollbacks_by_code:
            self.rollbacks_by_code[event.code_hash] += 1
        else:
            self.rollbacks_by_code[event.code_hash] = 1