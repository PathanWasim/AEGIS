"""
Trust policy definitions for AEGIS.

This module defines the policies and thresholds used by the trust
management system to determine when code is eligible for optimized
execution.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class TrustPolicy:
    """
    Trust policy configuration for AEGIS.
    
    This class defines the rules and thresholds used to calculate
    trust scores and determine optimization eligibility.
    """
    
    # Trust score thresholds
    TRUST_THRESHOLD_OPTIMIZATION: float = 1.0  # Minimum score for optimization
    TRUST_THRESHOLD_HIGH: float = 2.0          # High trust level
    TRUST_THRESHOLD_MEDIUM: float = 1.0        # Medium trust level  
    TRUST_THRESHOLD_LOW: float = 0.5           # Low trust level
    
    # Trust score adjustments
    TRUST_INCREMENT_BASE: float = 0.1          # Base increment per successful execution
    TRUST_INCREMENT_BONUS_CONSISTENT: float = 0.05  # Bonus for consistent success
    TRUST_INCREMENT_BONUS_EFFICIENT: float = 0.02   # Bonus for efficient execution
    TRUST_INCREMENT_BONUS_FAST: float = 0.02        # Bonus for fast execution
    
    TRUST_DECREMENT_VIOLATION: float = 0.5     # Penalty for security violations
    TRUST_DECREMENT_REPEATED: float = 0.2      # Additional penalty for repeated violations
    
    # Execution requirements
    MIN_EXECUTIONS_FOR_OPTIMIZATION: int = 3   # Minimum executions before optimization
    MIN_SUCCESS_RATE: float = 0.8             # Minimum success rate (80%)
    
    # Performance thresholds for bonuses
    EFFICIENT_INSTRUCTION_THRESHOLD: int = 100  # Instructions for efficiency bonus
    FAST_EXECUTION_THRESHOLD: float = 0.1      # Seconds for speed bonus
    
    # Trust score limits
    MAX_TRUST_SCORE: float = 10.0             # Maximum possible trust score
    MIN_TRUST_SCORE: float = 0.0              # Minimum possible trust score
    
    # History and persistence
    MAX_HISTORY_ENTRIES: int = 50             # Maximum history entries per code
    TRUST_DATA_CLEANUP_DAYS: int = 30         # Days before cleaning up unused trust data
    
    @classmethod
    def get_default_config(cls) -> Dict[str, Any]:
        """
        Get default trust policy configuration.
        
        Returns:
            Dictionary with default policy values
        """
        return {
            'trust_threshold_optimization': cls.TRUST_THRESHOLD_OPTIMIZATION,
            'trust_threshold_high': cls.TRUST_THRESHOLD_HIGH,
            'trust_threshold_medium': cls.TRUST_THRESHOLD_MEDIUM,
            'trust_threshold_low': cls.TRUST_THRESHOLD_LOW,
            'trust_increment_base': cls.TRUST_INCREMENT_BASE,
            'trust_increment_bonus_consistent': cls.TRUST_INCREMENT_BONUS_CONSISTENT,
            'trust_increment_bonus_efficient': cls.TRUST_INCREMENT_BONUS_EFFICIENT,
            'trust_increment_bonus_fast': cls.TRUST_INCREMENT_BONUS_FAST,
            'trust_decrement_violation': cls.TRUST_DECREMENT_VIOLATION,
            'trust_decrement_repeated': cls.TRUST_DECREMENT_REPEATED,
            'min_executions_for_optimization': cls.MIN_EXECUTIONS_FOR_OPTIMIZATION,
            'min_success_rate': cls.MIN_SUCCESS_RATE,
            'efficient_instruction_threshold': cls.EFFICIENT_INSTRUCTION_THRESHOLD,
            'fast_execution_threshold': cls.FAST_EXECUTION_THRESHOLD,
            'max_trust_score': cls.MAX_TRUST_SCORE,
            'min_trust_score': cls.MIN_TRUST_SCORE,
            'max_history_entries': cls.MAX_HISTORY_ENTRIES,
            'trust_data_cleanup_days': cls.TRUST_DATA_CLEANUP_DAYS
        }
    
    @classmethod
    def create_custom_policy(cls, **overrides) -> 'TrustPolicy':
        """
        Create a custom trust policy with specific overrides.
        
        Args:
            **overrides: Policy values to override
            
        Returns:
            TrustPolicy instance with custom values
        """
        config = cls.get_default_config()
        config.update(overrides)
        
        policy = cls()
        for key, value in config.items():
            if hasattr(policy, key.upper()):
                setattr(policy, key.upper(), value)
        
        return policy
    
    def validate_trust_score(self, score: float) -> float:
        """
        Validate and clamp trust score to valid range.
        
        Args:
            score: Trust score to validate
            
        Returns:
            Clamped trust score within valid range
        """
        return max(self.MIN_TRUST_SCORE, min(self.MAX_TRUST_SCORE, score))
    
    def calculate_trust_increment(self, execution_count: int, successful_count: int,
                                instruction_count: int, execution_time: float) -> float:
        """
        Calculate trust increment for successful execution.
        
        Args:
            execution_count: Total number of executions
            successful_count: Number of successful executions
            instruction_count: Instructions in this execution
            execution_time: Time taken for execution
            
        Returns:
            Trust increment amount
        """
        increment = self.TRUST_INCREMENT_BASE
        
        # Bonus for consistent successful executions
        if successful_count > 5:
            increment += self.TRUST_INCREMENT_BONUS_CONSISTENT
        
        # Bonus for efficient execution
        if instruction_count < self.EFFICIENT_INSTRUCTION_THRESHOLD:
            increment += self.TRUST_INCREMENT_BONUS_EFFICIENT
        
        # Bonus for fast execution
        if execution_time < self.FAST_EXECUTION_THRESHOLD:
            increment += self.TRUST_INCREMENT_BONUS_FAST
        
        return increment
    
    def calculate_trust_decrement(self, violation_count: int) -> float:
        """
        Calculate trust decrement for violations.
        
        Args:
            violation_count: Number of violations so far
            
        Returns:
            Trust decrement amount
        """
        decrement = self.TRUST_DECREMENT_VIOLATION
        
        # Additional penalty for repeated violations
        if violation_count > 1:
            decrement += self.TRUST_DECREMENT_REPEATED * (violation_count - 1)
        
        return decrement
    
    def is_eligible_for_optimization(self, score: float, execution_count: int,
                                   successful_count: int) -> bool:
        """
        Check if code is eligible for optimization based on policy.
        
        Args:
            score: Current trust score
            execution_count: Total executions
            successful_count: Successful executions
            
        Returns:
            True if eligible for optimization
        """
        # Must meet minimum score threshold
        if score < self.TRUST_THRESHOLD_OPTIMIZATION:
            return False
        
        # Must have sufficient execution history
        if execution_count < self.MIN_EXECUTIONS_FOR_OPTIMIZATION:
            return False
        
        # Must have good success rate
        if execution_count > 0:
            success_rate = successful_count / execution_count
            if success_rate < self.MIN_SUCCESS_RATE:
                return False
        
        return True
    
    def get_trust_level_name(self, score: float) -> str:
        """
        Get descriptive name for trust level.
        
        Args:
            score: Trust score
            
        Returns:
            Trust level name (NONE, LOW, MEDIUM, HIGH)
        """
        if score >= self.TRUST_THRESHOLD_HIGH:
            return "HIGH"
        elif score >= self.TRUST_THRESHOLD_MEDIUM:
            return "MEDIUM"
        elif score >= self.TRUST_THRESHOLD_LOW:
            return "LOW"
        else:
            return "NONE"


# Default policy instance
DEFAULT_TRUST_POLICY = TrustPolicy()