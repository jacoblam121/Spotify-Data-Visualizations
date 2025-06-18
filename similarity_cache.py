#!/usr/bin/env python3
"""
Enhanced Similarity Caching System
==================================
Persistent caching for similarity API calls to avoid re-fetching data.
Enables users to change timeframes/artist counts without waiting for API calls.
"""

import json
import time
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

class SimilarityCacheManager:
    """Enhanced caching manager for similarity API responses."""
    
    def __init__(self, cache_dir: str = "similarity_cache", cache_ttl_hours: int = 24 * 7):  # 1 week default
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
            cache_ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_ttl_seconds = cache_ttl_hours * 3600
        
        # Create subdirectories for different API sources
        (self.cache_dir / "lastfm").mkdir(exist_ok=True)
        (self.cache_dir / "deezer").mkdir(exist_ok=True)
        (self.cache_dir / "ultimate").mkdir(exist_ok=True)
        
        logger.info(f"Similarity cache initialized: {self.cache_dir}")
        logger.info(f"Cache TTL: {cache_ttl_hours} hours")
    
    def _generate_cache_key(self, artist_name: str, source: str, **kwargs) -> str:
        """Generate a unique cache key for the request."""
        # Include all parameters that affect the result
        cache_data = {
            'artist': artist_name.lower().strip(),
            'source': source,
            **kwargs
        }
        
        # Create hash of the request parameters
        cache_str = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_str.encode()).hexdigest()
        
        return f"{source}_{cache_hash}.json"
    
    def _get_cache_path(self, cache_key: str, source: str) -> Path:
        """Get the full path for a cache file."""
        return self.cache_dir / source / cache_key
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file exists and is not expired."""
        if not cache_path.exists():
            return False
        
        # Check if cache is expired
        file_age = time.time() - cache_path.stat().st_mtime
        return file_age < self.cache_ttl_seconds
    
    def get_cached_similarities(self, artist_name: str, source: str, **kwargs) -> Optional[List[Dict]]:
        """
        Get cached similarity results.
        
        Args:
            artist_name: Artist to search for
            source: API source (lastfm, deezer, ultimate)
            **kwargs: Additional parameters (limit, threshold, etc.)
            
        Returns:
            Cached similarities or None if not found/expired
        """
        cache_key = self._generate_cache_key(artist_name, source, **kwargs)
        cache_path = self._get_cache_path(cache_key, source)
        
        if not self._is_cache_valid(cache_path):
            logger.debug(f"Cache miss for {artist_name} ({source})")
            return None
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            logger.debug(f"Cache hit for {artist_name} ({source}): {len(cache_data.get('similarities', []))} results")
            return cache_data.get('similarities', [])
            
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            logger.warning(f"Cache read error for {artist_name} ({source}): {e}")
            return None
    
    def cache_similarities(self, artist_name: str, source: str, similarities: List[Dict], **kwargs) -> None:
        """
        Cache similarity results.
        
        Args:
            artist_name: Artist that was searched
            source: API source (lastfm, deezer, ultimate)  
            similarities: Similarity results to cache
            **kwargs: Additional parameters used in the request
        """
        cache_key = self._generate_cache_key(artist_name, source, **kwargs)
        cache_path = self._get_cache_path(cache_key, source)
        
        cache_data = {
            'artist_name': artist_name,
            'source': source,
            'cached_at': time.time(),
            'parameters': kwargs,
            'similarities': similarities
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Cached {len(similarities)} similarities for {artist_name} ({source})")
            
        except Exception as e:
            logger.error(f"Cache write error for {artist_name} ({source}): {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = {
            'cache_dir': str(self.cache_dir),
            'ttl_hours': self.cache_ttl_seconds / 3600,
            'sources': {}
        }
        
        for source_dir in ['lastfm', 'deezer', 'ultimate']:
            source_path = self.cache_dir / source_dir
            cache_files = list(source_path.glob("*.json"))
            
            valid_files = 0
            expired_files = 0
            total_size = 0
            
            for cache_file in cache_files:
                total_size += cache_file.stat().st_size
                if self._is_cache_valid(cache_file):
                    valid_files += 1
                else:
                    expired_files += 1
            
            stats['sources'][source_dir] = {
                'total_files': len(cache_files),
                'valid_files': valid_files,
                'expired_files': expired_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2)
            }
        
        return stats
    
    def cleanup_expired_cache(self) -> int:
        """Remove expired cache files and return count of removed files."""
        removed_count = 0
        
        for source_dir in ['lastfm', 'deezer', 'ultimate']:
            source_path = self.cache_dir / source_dir
            cache_files = list(source_path.glob("*.json"))
            
            for cache_file in cache_files:
                if not self._is_cache_valid(cache_file):
                    try:
                        cache_file.unlink()
                        removed_count += 1
                        logger.debug(f"Removed expired cache file: {cache_file.name}")
                    except Exception as e:
                        logger.warning(f"Failed to remove expired cache file {cache_file}: {e}")
        
        if removed_count > 0:
            logger.info(f"Cleaned up {removed_count} expired cache files")
        
        return removed_count

def test_cache_system():
    """Test the caching system."""
    print("🧪 Testing Similarity Cache System")
    print("=" * 35)
    
    # Initialize cache
    cache = SimilarityCacheManager(cache_ttl_hours=24)
    
    # Test data
    test_artist = "Taylor Swift"
    test_similarities = [
        {"name": "Olivia Rodrigo", "match": 0.85, "source": "lastfm"},
        {"name": "Gracie Abrams", "match": 0.80, "source": "lastfm"}
    ]
    
    # Test caching
    print(f"\n📥 Caching similarities for {test_artist}...")
    cache.cache_similarities(test_artist, "lastfm", test_similarities, limit=20, threshold=0.1)
    
    # Test retrieval
    print(f"📤 Retrieving cached similarities...")
    cached_results = cache.get_cached_similarities(test_artist, "lastfm", limit=20, threshold=0.1)
    
    if cached_results:
        print(f"✅ Cache hit! Retrieved {len(cached_results)} similarities")
        for sim in cached_results:
            print(f"   - {sim['name']}: {sim['match']}")
    else:
        print("❌ Cache miss!")
    
    # Test cache stats
    print(f"\n📊 Cache Statistics:")
    stats = cache.get_cache_stats()
    for source, source_stats in stats['sources'].items():
        print(f"   {source}: {source_stats['valid_files']} files, {source_stats['total_size_mb']} MB")
    
    print(f"\n✅ Cache system test complete!")

if __name__ == "__main__":
    test_cache_system()