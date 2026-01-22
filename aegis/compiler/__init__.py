"""
Compiler module for AEGIS - Optimized execution for trusted code.

This module provides optimized execution capabilities for code that has
earned sufficient trust, including AST optimization, code caching, and
performance improvements while maintaining security monitoring.
"""

from .optimizer import OptimizedExecutor, ASTOptimizer, OptimizationResult
from .cache import CodeCache, CachedCode

__all__ = [
    'OptimizedExecutor', 
    'ASTOptimizer', 
    'OptimizationResult',
    'CodeCache', 
    'CachedCode'
]