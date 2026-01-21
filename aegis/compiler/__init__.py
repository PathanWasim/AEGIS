"""
Compiler module for AEGIS - Optimized execution for trusted code.
"""

from .optimizer import OptimizedExecutor
from .cache import CodeCache

__all__ = ['OptimizedExecutor', 'CodeCache']