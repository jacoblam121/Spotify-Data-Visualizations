#!/usr/bin/env python3
"""
Centralized Cache Manager with joblib Integration
================================================
Provides unified caching for expensive computations while maintaining compatibility
with existing JSON-based caches.

Features:
- Automatic caching of function results based on arguments
- Configuration-driven cache control
- Organized cache directory structure
- Easy cache management and clearing
"""

import os
import shutil
import hashlib
import logging
from pathlib import Path
from functools import wraps
from typing import Any, Callable, Optional

try:
    from joblib import Memory
    JOBLIB_AVAILABLE = True
except ImportError:
    JOBLIB_AVAILABLE = False
    Memory = None

from config_loader import AppConfig

logger = logging.getLogger(__name__)

class CacheManager:
    """Centralized cache management using joblib."""
    
    def __init__(self, config: Optional[AppConfig] = None):
        """Initialize cache manager with configuration."""
        if config is None:
            config = AppConfig()
        
        self.config = config
        self._memory = None
        self._cache_initialized = False
        
        # Get cache configuration
        self.cache_config = self._get_cache_config()
        
        # Initialize cache if enabled and joblib is available
        if self.cache_config['enabled'] and JOBLIB_AVAILABLE:
            self._initialize_cache()
        elif not JOBLIB_AVAILABLE:
            logger.warning("joblib not available - caching disabled")
    
    def _get_cache_config(self) -> dict:
        """Get cache configuration from config file."""
        try:
            # Check for global disable
            global_disable = self.config.get_bool('CachingSystem', 'DISABLE_ALL_CACHING', False)
            
            # Cache directory settings
            cache_root = self.config.get('CachingSystem', 'CACHE_ROOT', '.cache')
            joblib_cache_dir = self.config.get('CachingSystem', 'JOBLIB_CACHE_DIR', '.cache/joblib')
            
            # Make paths absolute
            cache_root = Path(cache_root).resolve()
            joblib_cache_dir = Path(joblib_cache_dir).resolve()
            
            # Verbosity setting
            verbosity = self.config.get_int('CachingSystem', 'CACHE_VERBOSITY', 0)
            
            return {
                'enabled': not global_disable,
                'cache_root': cache_root,
                'joblib_cache_dir': joblib_cache_dir,
                'verbosity': verbosity
            }
        except Exception as e:
            logger.warning(f"Error reading cache configuration: {e}")
            # Fallback to defaults
            return {
                'enabled': True,
                'cache_root': Path('.cache').resolve(),
                'joblib_cache_dir': Path('.cache/joblib').resolve(),
                'verbosity': 0
            }
    
    def _initialize_cache(self):
        """Initialize joblib Memory instance."""
        try:
            # Create cache directory if it doesn't exist
            self.cache_config['joblib_cache_dir'].mkdir(parents=True, exist_ok=True)
            
            # Initialize joblib Memory
            self._memory = Memory(
                location=str(self.cache_config['joblib_cache_dir']),
                verbose=self.cache_config['verbosity'],
                mmap_mode='r'  # Memory-map mode for large arrays
            )
            
            self._cache_initialized = True
            logger.info(f"Cache initialized: {self.cache_config['joblib_cache_dir']}")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache: {e}")
            self._cache_initialized = False
    
    @property
    def is_enabled(self) -> bool:
        """Check if caching is enabled and available."""
        return (self.cache_config['enabled'] and 
                JOBLIB_AVAILABLE and 
                self._cache_initialized)
    
    def cache_result(self, func: Callable) -> Callable:
        """
        Decorator to cache function results.
        
        Usage:
            @cache_manager.cache_result
            def expensive_function(arg1, arg2):
                # ... expensive computation ...
                return result
        """
        if not self.is_enabled:
            logger.debug(f"Caching disabled for {func.__name__}")
            return func
        
        # Use joblib's caching
        cached_func = self._memory.cache(func)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = cached_func(*args, **kwargs)
                logger.debug(f"Cache hit/miss for {func.__name__}")
                return result
            except Exception as e:
                logger.warning(f"Cache error for {func.__name__}: {e}")
                # Fallback to direct function call
                return func(*args, **kwargs)
        
        return wrapper
    
    def clear_cache(self, confirm: bool = True) -> bool:
        """
        Clear all joblib caches.
        
        Args:
            confirm: Whether to require confirmation
            
        Returns:
            True if cache was cleared, False otherwise
        """
        if not self._cache_initialized:
            logger.info("No cache to clear")
            return False
        
        if confirm:
            cache_dir = self.cache_config['joblib_cache_dir']
            response = input(f"Clear cache directory {cache_dir}? (y/n): ")
            if response.lower() != 'y':
                print("Cache clear cancelled")
                return False
        
        try:
            # Clear joblib cache
            if self._memory:
                self._memory.clear()
            
            # Remove cache directory
            cache_dir = self.cache_config['joblib_cache_dir']
            if cache_dir.exists():
                shutil.rmtree(cache_dir)
                logger.info(f"Cleared cache directory: {cache_dir}")
            
            # Reinitialize
            self._initialize_cache()
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def get_cache_info(self) -> dict:
        """Get information about the cache."""
        info = {
            'enabled': self.is_enabled,
            'joblib_available': JOBLIB_AVAILABLE,
            'cache_initialized': self._cache_initialized,
            'config': self.cache_config
        }
        
        if self._cache_initialized:
            cache_dir = self.cache_config['joblib_cache_dir']
            if cache_dir.exists():
                # Count cache files
                cache_files = list(cache_dir.rglob('*.pkl'))
                total_size = sum(f.stat().st_size for f in cache_files)
                info.update({
                    'cache_files': len(cache_files),
                    'cache_size_mb': round(total_size / (1024 * 1024), 2)
                })
            else:
                info.update({
                    'cache_files': 0,
                    'cache_size_mb': 0
                })
        
        return info


# Global cache manager instance
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get the global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

# Convenience decorator function
def cache_result(func: Callable) -> Callable:
    """
    Convenience decorator for caching function results.
    
    Usage:
        from cache_manager import cache_result
        
        @cache_result
        def expensive_function(arg1, arg2):
            # ... expensive computation ...
            return result
    """
    return get_cache_manager().cache_result(func)


def main():
    """Test and demonstrate cache functionality."""
    import time
    
    print("🔧 Cache Manager Test")
    print("=" * 40)
    
    # Get cache manager
    cm = get_cache_manager()
    
    # Show cache info
    info = cm.get_cache_info()
    print(f"Cache enabled: {info['enabled']}")
    print(f"Cache directory: {info['config']['joblib_cache_dir']}")
    
    if not info['enabled']:
        print("❌ Caching is disabled or joblib not available")
        return
    
    # Test function
    @cm.cache_result
    def slow_function(n: int) -> int:
        """A deliberately slow function to test caching."""
        print(f"  Computing slow_function({n})...")
        time.sleep(1)  # Simulate slow computation
        return n * n
    
    print("\n🧪 Testing cache functionality:")
    
    # First call (should be slow)
    start = time.time()
    result1 = slow_function(5)
    time1 = time.time() - start
    print(f"First call: {result1} (took {time1:.2f}s)")
    
    # Second call (should be fast - cached)
    start = time.time()
    result2 = slow_function(5)
    time2 = time.time() - start
    print(f"Second call: {result2} (took {time2:.3f}s)")
    
    # Show cache info again
    info = cm.get_cache_info()
    print(f"\nCache files: {info.get('cache_files', 'N/A')}")
    print(f"Cache size: {info.get('cache_size_mb', 'N/A')} MB")
    
    print("\n✅ Cache test complete!")


if __name__ == "__main__":
    main()