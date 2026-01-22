"""
Trust management implementation for AEGIS.

This module manages trust scores for code execution, determining when
code has earned enough trust to be executed in optimized mode rather
than the default sandboxed interpreter.
"""

import hashlib
import json
import os
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..runtime.monitor import ExecutionMetrics, SecurityViolation


@dataclass
class TrustScore:
    """
    Represents trust level for a specific piece of code.
    
    Trust scores track the execution history and safety record
    of code to determine eligibility for optimized execution.
    """
    code_hash: str
    current_score: float = 0.0
    execution_count: int = 0
    successful_executions: int = 0
    violation_count: int = 0
    last_execution: Optional[datetime] = None
    last_violation: Optional[datetime] = None
    first_execution: Optional[datetime] = None
    trust_history: List[Dict[str, Any]] = field(default_factory=list)
    
    def add_execution_result(self, metrics: ExecutionMetrics, had_violations: bool = False) -> None:
        """
        Record the result of an execution and update trust score.
        
        Args:
            metrics: Execution metrics from the runtime monitor
            had_violations: Whether security violations occurred
        """
        now = datetime.now()
        
        # Update execution tracking
        self.execution_count += 1
        self.last_execution = now
        
        if self.first_execution is None:
            self.first_execution = now
        
        # Update violation tracking
        if had_violations or len(metrics.violations_detected) > 0:
            self.violation_count += 1
            self.last_violation = now
            # Decrease trust on violations
            self._decrease_trust("security_violation")
        else:
            self.successful_executions += 1
            # Increase trust on successful execution
            self._increase_trust("successful_execution", metrics)
        
        # Record in history
        self.trust_history.append({
            'timestamp': now.isoformat(),
            'score_before': self.current_score,
            'score_after': self.current_score,
            'execution_count': self.execution_count,
            'had_violations': had_violations,
            'instruction_count': metrics.instruction_count,
            'execution_time': metrics.execution_time
        })
        
        # Keep only recent history (last 50 executions)
        if len(self.trust_history) > 50:
            self.trust_history = self.trust_history[-50:]
    
    def _increase_trust(self, reason: str, metrics: ExecutionMetrics) -> None:
        """
        Increase trust score based on successful execution.
        
        Args:
            reason: Reason for trust increase
            metrics: Execution metrics
        """
        # Base increment
        increment = 0.1
        
        # Bonus for consistent successful executions
        if self.successful_executions > 5:
            increment += 0.05
        
        # Bonus for efficient execution (low instruction count)
        if metrics.instruction_count < 100:
            increment += 0.02
        
        # Bonus for fast execution
        if metrics.execution_time < 0.1:
            increment += 0.02
        
        # Apply increment with maximum cap
        old_score = self.current_score
        self.current_score = min(10.0, self.current_score + increment)
        
        # Update history entry
        if self.trust_history:
            self.trust_history[-1]['score_after'] = self.current_score
            self.trust_history[-1]['increment'] = self.current_score - old_score
            self.trust_history[-1]['reason'] = reason
    
    def _decrease_trust(self, reason: str) -> None:
        """
        Decrease trust score due to violations or failures.
        
        Args:
            reason: Reason for trust decrease
        """
        # Significant penalty for violations
        decrement = 0.5
        
        # Larger penalty for repeated violations
        if self.violation_count > 1:
            decrement += 0.2 * (self.violation_count - 1)
        
        # Apply decrement with minimum floor
        old_score = self.current_score
        self.current_score = max(0.0, self.current_score - decrement)
        
        # Update history entry
        if self.trust_history:
            self.trust_history[-1]['score_after'] = self.current_score
            self.trust_history[-1]['decrement'] = old_score - self.current_score
            self.trust_history[-1]['reason'] = reason
    
    def get_trust_level(self) -> str:
        """
        Get descriptive trust level.
        
        Returns:
            String description of current trust level
        """
        if self.current_score >= 2.0:
            return "HIGH"
        elif self.current_score >= 1.0:
            return "MEDIUM"
        elif self.current_score >= 0.5:
            return "LOW"
        else:
            return "NONE"
    
    def is_eligible_for_optimization(self, threshold: float = 1.0) -> bool:
        """
        Check if code is eligible for optimized execution.
        
        Args:
            threshold: Minimum trust score required
            
        Returns:
            True if eligible for optimization
        """
        # Must meet minimum score threshold
        if self.current_score < threshold:
            return False
        
        # Must have sufficient execution history
        if self.execution_count < 3:
            return False
        
        # Must have recent successful executions
        if self.last_violation and self.last_execution:
            # If last violation was more recent than last execution, not eligible
            if self.last_violation > self.last_execution:
                return False
        
        # Must have good success rate
        success_rate = self.successful_executions / self.execution_count
        if success_rate < 0.8:  # 80% success rate required
            return False
        
        return True
    
    def reset_trust(self, reason: str = "manual_reset") -> None:
        """
        Reset trust score to zero.
        
        Args:
            reason: Reason for reset
        """
        old_score = self.current_score
        self.current_score = 0.0
        
        # Record reset in history
        self.trust_history.append({
            'timestamp': datetime.now().isoformat(),
            'score_before': old_score,
            'score_after': 0.0,
            'reason': reason,
            'reset': True
        })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        if self.last_execution:
            data['last_execution'] = self.last_execution.isoformat()
        if self.last_violation:
            data['last_violation'] = self.last_violation.isoformat()
        if self.first_execution:
            data['first_execution'] = self.first_execution.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrustScore':
        """Create from dictionary."""
        # Convert ISO strings back to datetime objects
        if data.get('last_execution'):
            data['last_execution'] = datetime.fromisoformat(data['last_execution'])
        if data.get('last_violation'):
            data['last_violation'] = datetime.fromisoformat(data['last_violation'])
        if data.get('first_execution'):
            data['first_execution'] = datetime.fromisoformat(data['first_execution'])
        
        return cls(**data)


class TrustManager:
    """
    Trust manager for AEGIS programs.
    
    This manager tracks trust scores for code and determines when
    code has earned sufficient trust to be executed in optimized
    mode rather than the default sandboxed interpreter.
    
    Key responsibilities:
    - Calculate and maintain trust scores for code
    - Determine optimization eligibility based on trust
    - Persist trust data across sessions
    - Provide trust visibility through logging
    """
    
    def __init__(self, trust_file: str = ".aegis_trust.json"):
        """
        Initialize the trust manager.
        
        Args:
            trust_file: File path for persisting trust data
        """
        self.trust_file = trust_file
        self.trust_scores: Dict[str, TrustScore] = {}
        self.trust_threshold = 1.0
        self.optimization_enabled = True
        
        # Load existing trust data
        self._load_trust_data()
    
    def get_code_hash(self, source_code: str) -> str:
        """
        Generate a hash for source code to track trust.
        
        Args:
            source_code: The source code to hash
            
        Returns:
            SHA-256 hash of the source code
        """
        return hashlib.sha256(source_code.encode('utf-8')).hexdigest()[:16]
    
    def get_trust_score(self, code_hash: str) -> TrustScore:
        """
        Get trust score for code.
        
        Args:
            code_hash: Hash of the code
            
        Returns:
            TrustScore object for the code
        """
        if code_hash not in self.trust_scores:
            self.trust_scores[code_hash] = TrustScore(code_hash=code_hash)
        
        return self.trust_scores[code_hash]
    
    def update_trust(self, code_hash: str, metrics: ExecutionMetrics, 
                    violations: List[SecurityViolation] = None) -> float:
        """
        Update trust score based on execution results.
        
        Args:
            code_hash: Hash of the executed code
            metrics: Execution metrics from runtime monitor
            violations: List of security violations (if any)
            
        Returns:
            Updated trust score
        """
        trust_score = self.get_trust_score(code_hash)
        had_violations = violations and len(violations) > 0
        
        # Record execution result
        trust_score.add_execution_result(metrics, had_violations)
        
        # Log trust change
        self._log_trust_change(code_hash, trust_score, had_violations)
        
        # Persist updated trust data
        self._save_trust_data()
        
        return trust_score.current_score
    
    def is_trusted_for_optimization(self, code_hash: str) -> bool:
        """
        Check if code is trusted for optimized execution.
        
        Args:
            code_hash: Hash of the code
            
        Returns:
            True if code should be executed in optimized mode
        """
        if not self.optimization_enabled:
            return False
        
        trust_score = self.get_trust_score(code_hash)
        return trust_score.is_eligible_for_optimization(self.trust_threshold)
    
    def revoke_trust_for_violation(self, code_hash: str, violation_type: str, details: str) -> None:
        """
        Revoke trust for specific code due to security violation.
        
        Args:
            code_hash: Hash of the code
            violation_type: Type of security violation
            details: Details about the violation
        """
        if code_hash in self.trust_scores:
            old_score = self.trust_scores[code_hash].current_score
            self.trust_scores[code_hash].reset_trust(f"security_violation_{violation_type}")
            
            print(f"[TRUST] Revoked trust for code {code_hash[:8]}... "
                  f"(was {old_score:.2f}, now 0.00) - {violation_type}: {details}")
            
            self._save_trust_data()
        else:
            # Create new trust score with violation
            trust_score = TrustScore(code_hash=code_hash)
            trust_score.reset_trust(f"security_violation_{violation_type}")
            self.trust_scores[code_hash] = trust_score
            
            print(f"[TRUST] Created new trust record for code {code_hash[:8]}... "
                  f"with violation - {violation_type}: {details}")
            
            self._save_trust_data()
    
    def revoke_trust(self, code_hash: str, reason: str = "manual_revocation") -> None:
        """
        Revoke trust for specific code.
        
        Args:
            code_hash: Hash of the code
            reason: Reason for revocation
        """
        if code_hash in self.trust_scores:
            old_score = self.trust_scores[code_hash].current_score
            self.trust_scores[code_hash].reset_trust(reason)
            
            print(f"[TRUST] Revoked trust for code {code_hash[:8]}... "
                  f"(was {old_score:.2f}, now 0.00) - {reason}")
            
            self._save_trust_data()
    
    def get_trust_summary(self) -> Dict[str, Any]:
        """
        Get summary of all trust scores.
        
        Returns:
            Dictionary with trust statistics
        """
        if not self.trust_scores:
            return {
                'total_codes': 0,
                'trusted_codes': 0,
                'average_score': 0.0,
                'trust_levels': {'NONE': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
            }
        
        scores = [ts.current_score for ts in self.trust_scores.values()]
        trusted_count = sum(1 for ts in self.trust_scores.values() 
                           if ts.is_eligible_for_optimization(self.trust_threshold))
        
        trust_levels = {'NONE': 0, 'LOW': 0, 'MEDIUM': 0, 'HIGH': 0}
        for ts in self.trust_scores.values():
            trust_levels[ts.get_trust_level()] += 1
        
        return {
            'total_codes': len(self.trust_scores),
            'trusted_codes': trusted_count,
            'average_score': sum(scores) / len(scores),
            'trust_levels': trust_levels,
            'optimization_enabled': self.optimization_enabled,
            'trust_threshold': self.trust_threshold
        }
    
    def set_trust_threshold(self, threshold: float) -> None:
        """
        Set the trust threshold for optimization.
        
        Args:
            threshold: Minimum trust score required for optimization
        """
        old_threshold = self.trust_threshold
        self.trust_threshold = max(0.0, min(10.0, threshold))
        
        print(f"[TRUST] Threshold changed from {old_threshold:.2f} to {self.trust_threshold:.2f}")
    
    def enable_optimization(self, enabled: bool = True) -> None:
        """
        Enable or disable trust-based optimization.
        
        Args:
            enabled: Whether to enable optimization
        """
        self.optimization_enabled = enabled
        status = "enabled" if enabled else "disabled"
        print(f"[TRUST] Optimization {status}")
    
    def _log_trust_change(self, code_hash: str, trust_score: TrustScore, had_violations: bool) -> None:
        """
        Log trust score changes to console.
        
        Args:
            code_hash: Hash of the code
            trust_score: Updated trust score
            had_violations: Whether violations occurred
        """
        short_hash = code_hash[:8]
        score = trust_score.current_score
        level = trust_score.get_trust_level()
        
        if had_violations:
            print(f"[TRUST] Code {short_hash}... trust decreased to {score:.2f} ({level}) - violations detected")
        else:
            print(f"[TRUST] Code {short_hash}... trust increased to {score:.2f} ({level}) - successful execution")
        
        # Log optimization eligibility changes
        if trust_score.is_eligible_for_optimization(self.trust_threshold):
            if trust_score.execution_count == 3:  # First time becoming eligible
                print(f"[TRUST] Code {short_hash}... now eligible for optimized execution")
    
    def _save_trust_data(self) -> None:
        """Save trust data to file."""
        try:
            data = {
                'trust_scores': {k: v.to_dict() for k, v in self.trust_scores.items()},
                'trust_threshold': self.trust_threshold,
                'optimization_enabled': self.optimization_enabled,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.trust_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            print(f"[TRUST] Warning: Could not save trust data - {e}")
    
    def _load_trust_data(self) -> None:
        """Load trust data from file."""
        try:
            if os.path.exists(self.trust_file):
                with open(self.trust_file, 'r') as f:
                    data = json.load(f)
                
                # Load trust scores
                for code_hash, score_data in data.get('trust_scores', {}).items():
                    self.trust_scores[code_hash] = TrustScore.from_dict(score_data)
                
                # Load configuration
                self.trust_threshold = data.get('trust_threshold', 1.0)
                self.optimization_enabled = data.get('optimization_enabled', True)
                
                print(f"[TRUST] Loaded {len(self.trust_scores)} trust scores from {self.trust_file}")
                
        except Exception as e:
            print(f"[TRUST] Warning: Could not load trust data - {e}")
            # Continue with empty trust scores
    
    def cleanup_old_trust_data(self, days: int = 30) -> None:
        """
        Remove trust data for code that hasn't been executed recently.
        
        Args:
            days: Number of days after which to remove unused trust data
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        codes_to_remove = []
        
        for code_hash, trust_score in self.trust_scores.items():
            if (trust_score.last_execution is None or 
                trust_score.last_execution < cutoff_date):
                codes_to_remove.append(code_hash)
        
        for code_hash in codes_to_remove:
            del self.trust_scores[code_hash]
        
        if codes_to_remove:
            print(f"[TRUST] Cleaned up {len(codes_to_remove)} old trust records")
            self._save_trust_data()