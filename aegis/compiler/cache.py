"""
Code cache implementation for AEGIS optimized execution.

This module provides caching for compiled representations of trusted code,
enabling faster execution through pre-compiled optimizations.
"""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..ast.nodes import ASTNode


@dataclass
class CachedCode:
    """
    Represents cached compiled code with metadata.
    
    This stores the optimized representation of code along with
    compilation metadata and performance statistics.
    """
    code_hash: str
    original_ast: List[ASTNode]
    optimized_ast: List[ASTNode]
    compilation_time: float
    created_at: datetime
    last_accessed: datetime
    access_count: int = 0
    optimization_flags: Dict[str, bool] = field(default_factory=dict)
    performance_stats: Dict[str, float] = field(default_factory=dict)
    
    def mark_accessed(self) -> None:
        """Mark this cached code as accessed."""
        self.last_accessed = datetime.now()
        self.access_count += 1
    
    def get_age_seconds(self) -> float:
        """Get age of cached code in seconds."""
        return (datetime.now() - self.created_at).total_seconds()
    
    def get_last_access_seconds(self) -> float:
        """Get seconds since last access."""
        return (datetime.now() - self.last_accessed).total_seconds()


class CodeCache:
    """
    Code caching system for optimized execution.
    
    This cache stores compiled representations of trusted code to enable
    faster execution. It includes cache management, eviction policies,
    and performance tracking.
    
    Key responsibilities:
    - Store optimized AST representations
    - Track compilation and access statistics
    - Manage cache size and eviction
    - Provide cache hit/miss metrics
    """
    
    def __init__(self, max_size: int = 100, max_age_hours: int = 24):
        """
        Initialize the code cache.
        
        Args:
            max_size: Maximum number of cached entries
            max_age_hours: Maximum age of cached entries in hours
        """
        self.cache: Dict[str, CachedCode] = {}
        self.max_size = max_size
        self.max_age = timedelta(hours=max_age_hours)
        
        # Performance metrics
        self.cache_hits = 0
        self.cache_misses = 0
        self.evictions = 0
        self.compilations = 0
    
    def get(self, code_hash: str) -> Optional[CachedCode]:
        """
        Get cached code by hash.
        
        Args:
            code_hash: Hash of the code to retrieve
            
        Returns:
            CachedCode if found and valid, None otherwise
        """
        if code_hash not in self.cache:
            self.cache_misses += 1
            return None
        
        cached_code = self.cache[code_hash]
        
        # Check if cache entry is too old
        if cached_code.get_age_seconds() > self.max_age.total_seconds():
            self._evict(code_hash)
            self.cache_misses += 1
            return None
        
        # Mark as accessed and return
        cached_code.mark_accessed()
        self.cache_hits += 1
        return cached_code
    
    def put(self, code_hash: str, original_ast: List[ASTNode], 
            optimized_ast: List[ASTNode], compilation_time: float,
            optimization_flags: Dict[str, bool] = None) -> None:
        """
        Cache compiled code.
        
        Args:
            code_hash: Hash of the code
            original_ast: Original AST nodes
            optimized_ast: Optimized AST nodes
            compilation_time: Time taken to compile
            optimization_flags: Flags indicating applied optimizations
        """
        # Ensure cache size limit
        if len(self.cache) >= self.max_size:
            self._evict_lru()
        
        # Create cached entry
        now = datetime.now()
        cached_code = CachedCode(
            code_hash=code_hash,
            original_ast=original_ast,
            optimized_ast=optimized_ast,
            compilation_time=compilation_time,
            created_at=now,
            last_accessed=now,
            optimization_flags=optimization_flags or {}
        )
        
        self.cache[code_hash] = cached_code
        self.compilations += 1
        
        print(f"[CACHE] Cached optimized code {code_hash[:8]}... "
              f"(compilation: {compilation_time:.3f}s, size: {len(self.cache)})")
    
    def clear(self, code_hash: str) -> bool:
        """
        Clear specific cached code.
        
        Args:
            code_hash: Hash of the code to clear
            
        Returns:
            True if code was cached and cleared, False otherwise
        """
        if code_hash in self.cache:
            del self.cache[code_hash]
            print(f"[CACHE] Cleared cached code {code_hash[:8]}...")
            return True
        return False
    
    def clear_all(self) -> None:
        """Clear all cached code."""
        count = len(self.cache)
        self.cache.clear()
        print(f"[CACHE] Cleared all cached code ({count} entries)")
    
    def is_cached(self, code_hash: str) -> bool:
        """
        Check if code is cached and valid.
        
        Args:
            code_hash: Hash of the code to check
            
        Returns:
            True if code is cached and valid
        """
        return self.get(code_hash) is not None
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache performance statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests) if total_requests > 0 else 0.0
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'hit_rate': hit_rate,
            'evictions': self.evictions,
            'compilations': self.compilations,
            'total_requests': total_requests
        }
    
    def get_cached_entries_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all cached entries.
        
        Returns:
            List of dictionaries with entry information
        """
        entries = []
        for code_hash, cached_code in self.cache.items():
            entries.append({
                'code_hash': code_hash[:8] + '...',
                'age_seconds': cached_code.get_age_seconds(),
                'last_access_seconds': cached_code.get_last_access_seconds(),
                'access_count': cached_code.access_count,
                'compilation_time': cached_code.compilation_time,
                'optimization_flags': cached_code.optimization_flags,
                'ast_size': len(cached_code.optimized_ast)
            })
        
        # Sort by last access (most recent first)
        entries.sort(key=lambda x: x['last_access_seconds'])
        return entries
    
    def cleanup_expired(self) -> int:
        """
        Remove expired cache entries.
        
        Returns:
            Number of entries removed
        """
        expired_hashes = []
        max_age_seconds = self.max_age.total_seconds()
        
        for code_hash, cached_code in self.cache.items():
            if cached_code.get_age_seconds() > max_age_seconds:
                expired_hashes.append(code_hash)
        
        for code_hash in expired_hashes:
            del self.cache[code_hash]
            self.evictions += 1
        
        if expired_hashes:
            print(f"[CACHE] Cleaned up {len(expired_hashes)} expired entries")
        
        return len(expired_hashes)
    
    def _evict(self, code_hash: str) -> None:
        """Evict specific cache entry."""
        if code_hash in self.cache:
            del self.cache[code_hash]
            self.evictions += 1
    
    def _evict_lru(self) -> None:
        """Evict least recently used cache entry."""
        if not self.cache:
            return
        
        # Find LRU entry
        lru_hash = min(self.cache.keys(), 
                      key=lambda h: self.cache[h].last_accessed)
        
        print(f"[CACHE] Evicting LRU entry {lru_hash[:8]}... "
              f"(last accessed: {self.cache[lru_hash].get_last_access_seconds():.1f}s ago)")
        
        self._evict(lru_hash)
    
    def update_performance_stats(self, code_hash: str, 
                               execution_time: float, 
                               speedup_factor: float) -> None:
        """
        Update performance statistics for cached code.
        
        Args:
            code_hash: Hash of the executed code
            execution_time: Time taken to execute
            speedup_factor: Speedup compared to interpreted execution
        """
        if code_hash in self.cache:
            cached_code = self.cache[code_hash]
            stats = cached_code.performance_stats
            
            # Update running averages
            if 'avg_execution_time' not in stats:
                stats['avg_execution_time'] = execution_time
                stats['avg_speedup_factor'] = speedup_factor
                stats['execution_count'] = 1
            else:
                count = stats['execution_count']
                stats['avg_execution_time'] = (
                    (stats['avg_execution_time'] * count + execution_time) / (count + 1)
                )
                stats['avg_speedup_factor'] = (
                    (stats['avg_speedup_factor'] * count + speedup_factor) / (count + 1)
                )
                stats['execution_count'] = count + 1
            
            # Track best performance
            if 'best_execution_time' not in stats or execution_time < stats['best_execution_time']:
                stats['best_execution_time'] = execution_time
            
            if 'best_speedup_factor' not in stats or speedup_factor > stats['best_speedup_factor']:
                stats['best_speedup_factor'] = speedup_factor