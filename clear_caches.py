#!/usr/bin/env python3
"""
Cache Management Utility
========================
Clear all caches or specific cache types for the Spotify Data Visualizations project.

Usage:
    python clear_caches.py --all          # Clear all caches
    python clear_caches.py --joblib       # Clear only joblib caches
    python clear_caches.py --api          # Clear only API caches
    python clear_caches.py --network      # Clear only network generation caches
    python clear_caches.py --force        # Skip confirmation prompts

Cache Types:
- joblib: Function result caches (network generation, edge weighting)
- api: JSON API response caches (Last.fm, Spotify, etc.)
- network: Specific network generation results
"""

import os
import sys
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Any
import logging

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from cache_manager import get_cache_manager
    from config_loader import AppConfig
except ImportError as e:
    print(f"Error importing project modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

logger = logging.getLogger(__name__)

class CacheCleaner:
    """Utility for clearing different types of caches."""
    
    def __init__(self):
        """Initialize cache cleaner."""
        self.config = AppConfig()
        self.cache_manager = get_cache_manager()
        self.project_root = Path(__file__).parent
        
        # Define all cache directories
        self.cache_directories = {
            'joblib': self._get_joblib_cache_dir(),
            'api': self._get_api_cache_dirs(),
            'network': self._get_network_cache_dirs()
        }
    
    def _get_joblib_cache_dir(self) -> Path:
        """Get joblib cache directory."""
        try:
            return Path(self.config.get('CachingSystem', 'JOBLIB_CACHE_DIR', '.cache/joblib')).resolve()
        except:
            return self.project_root / '.cache' / 'joblib'
    
    def _get_api_cache_dirs(self) -> List[Path]:
        """Get all API cache directories."""
        api_cache_dirs = []
        
        # Known API cache directories
        known_dirs = [
            'lastfm_cache',
            'album_art_cache',
            'artist_art_cache',
            'musicbrainz_cache'
        ]
        
        for dir_name in known_dirs:
            cache_dir = self.project_root / dir_name
            if cache_dir.exists():
                api_cache_dirs.append(cache_dir)
        
        return api_cache_dirs
    
    def _get_network_cache_dirs(self) -> List[Path]:
        """Get network-specific cache directories."""
        network_cache_dirs = []
        
        # Known network cache directories
        known_dirs = [
            'similarity_cache',
            'network_cache'
        ]
        
        for dir_name in known_dirs:
            cache_dir = self.project_root / dir_name
            if cache_dir.exists():
                network_cache_dirs.append(cache_dir)
        
        return network_cache_dirs
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about all caches."""
        stats = {
            'joblib': self._get_dir_stats(self.cache_directories['joblib']),
            'api': self._get_multiple_dirs_stats(self.cache_directories['api']),
            'network': self._get_multiple_dirs_stats(self.cache_directories['network'])
        }
        
        return stats
    
    def _get_dir_stats(self, cache_dir: Path) -> Dict[str, Any]:
        """Get statistics for a single directory."""
        if not cache_dir.exists():
            return {'exists': False, 'files': 0, 'size_mb': 0}
        
        try:
            all_files = list(cache_dir.rglob('*'))
            cache_files = [f for f in all_files if f.is_file()]
            total_size = sum(f.stat().st_size for f in cache_files)
            
            return {
                'exists': True,
                'path': str(cache_dir),
                'files': len(cache_files),
                'size_mb': round(total_size / (1024 * 1024), 2)
            }
        except Exception as e:
            return {'exists': True, 'error': str(e), 'files': 0, 'size_mb': 0}
    
    def _get_multiple_dirs_stats(self, cache_dirs: List[Path]) -> Dict[str, Any]:
        """Get combined statistics for multiple directories."""
        total_files = 0
        total_size = 0
        existing_dirs = []
        
        for cache_dir in cache_dirs:
            stats = self._get_dir_stats(cache_dir)
            if stats['exists'] and 'error' not in stats:
                total_files += stats['files']
                total_size += stats['size_mb']
                existing_dirs.append(str(cache_dir))
        
        return {
            'directories': existing_dirs,
            'total_files': total_files,
            'total_size_mb': round(total_size, 2)
        }
    
    def clear_joblib_cache(self, force: bool = False) -> bool:
        """Clear joblib caches."""
        print("🔧 Clearing joblib caches...")
        
        try:
            success = self.cache_manager.clear_cache(confirm=not force)
            if success:
                print("✅ Joblib cache cleared")
            return success
        except Exception as e:
            print(f"❌ Error clearing joblib cache: {e}")
            return False
    
    def clear_api_caches(self, force: bool = False) -> bool:
        """Clear API caches."""
        print("📡 Clearing API caches...")
        
        api_dirs = self.cache_directories['api']
        if not api_dirs:
            print("📭 No API cache directories found")
            return True
        
        if not force:
            print(f"This will delete {len(api_dirs)} API cache directories:")
            for cache_dir in api_dirs:
                stats = self._get_dir_stats(cache_dir)
                print(f"  - {cache_dir} ({stats['files']} files, {stats['size_mb']} MB)")
            
            response = input("Continue? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled")
                return False
        
        cleared_count = 0
        for cache_dir in api_dirs:
            try:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    print(f"✅ Cleared {cache_dir}")
                    cleared_count += 1
            except Exception as e:
                print(f"❌ Failed to clear {cache_dir}: {e}")
        
        print(f"🧹 Cleared {cleared_count}/{len(api_dirs)} API cache directories")
        return cleared_count > 0
    
    def clear_network_caches(self, force: bool = False) -> bool:
        """Clear network-specific caches."""
        print("🕸️ Clearing network caches...")
        
        network_dirs = self.cache_directories['network']
        if not network_dirs:
            print("📭 No network cache directories found")
            return True
        
        if not force:
            print(f"This will delete {len(network_dirs)} network cache directories:")
            for cache_dir in network_dirs:
                stats = self._get_dir_stats(cache_dir)
                print(f"  - {cache_dir} ({stats['files']} files, {stats['size_mb']} MB)")
            
            response = input("Continue? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled")
                return False
        
        cleared_count = 0
        for cache_dir in network_dirs:
            try:
                if cache_dir.exists():
                    shutil.rmtree(cache_dir)
                    print(f"✅ Cleared {cache_dir}")
                    cleared_count += 1
            except Exception as e:
                print(f"❌ Failed to clear {cache_dir}: {e}")
        
        print(f"🧹 Cleared {cleared_count}/{len(network_dirs)} network cache directories")
        return cleared_count > 0
    
    def clear_all_caches(self, force: bool = False) -> bool:
        """Clear all caches."""
        print("🧹 Clearing ALL caches...")
        
        if not force:
            stats = self.get_cache_stats()
            total_files = (stats['joblib']['files'] + 
                          stats['api']['total_files'] + 
                          stats['network']['total_files'])
            total_size = (stats['joblib']['size_mb'] + 
                         stats['api']['total_size_mb'] + 
                         stats['network']['total_size_mb'])
            
            print(f"This will delete approximately {total_files} files ({total_size:.1f} MB)")
            response = input("Are you sure? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled")
                return False
        
        success_count = 0
        
        # Clear each cache type
        if self.clear_joblib_cache(force=True):
            success_count += 1
        
        if self.clear_api_caches(force=True):
            success_count += 1
        
        if self.clear_network_caches(force=True):
            success_count += 1
        
        print(f"\n🎉 Cache clearing complete! ({success_count}/3 operations successful)")
        return success_count > 0


def main():
    """Main entry point for cache clearing utility."""
    parser = argparse.ArgumentParser(
        description="Clear caches for Spotify Data Visualizations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python clear_caches.py --all          # Clear all caches
  python clear_caches.py --joblib       # Clear only joblib caches
  python clear_caches.py --api          # Clear only API caches
  python clear_caches.py --network      # Clear only network caches
  python clear_caches.py --stats        # Show cache statistics
        """
    )
    
    # Action group (mutually exclusive)
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument('--all', action='store_true', help='Clear all caches')
    action_group.add_argument('--joblib', action='store_true', help='Clear joblib caches only')
    action_group.add_argument('--api', action='store_true', help='Clear API caches only')
    action_group.add_argument('--network', action='store_true', help='Clear network caches only')
    action_group.add_argument('--stats', action='store_true', help='Show cache statistics')
    
    # Options
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    
    # Initialize cache cleaner
    try:
        cleaner = CacheCleaner()
    except Exception as e:
        print(f"❌ Failed to initialize cache cleaner: {e}")
        sys.exit(1)
    
    # Execute requested action
    if args.stats:
        print("📊 Cache Statistics")
        print("=" * 40)
        
        stats = cleaner.get_cache_stats()
        
        print(f"\n🔧 Joblib Cache:")
        if stats['joblib']['exists']:
            print(f"  Path: {stats['joblib']['path']}")
            print(f"  Files: {stats['joblib']['files']}")
            print(f"  Size: {stats['joblib']['size_mb']} MB")
        else:
            print("  No joblib cache found")
        
        print(f"\n📡 API Caches:")
        if stats['api']['directories']:
            for directory in stats['api']['directories']:
                dir_stats = cleaner._get_dir_stats(Path(directory))
                print(f"  {directory}: {dir_stats['files']} files, {dir_stats['size_mb']} MB")
            print(f"  Total: {stats['api']['total_files']} files, {stats['api']['total_size_mb']} MB")
        else:
            print("  No API caches found")
        
        print(f"\n🕸️ Network Caches:")
        if stats['network']['directories']:
            for directory in stats['network']['directories']:
                dir_stats = cleaner._get_dir_stats(Path(directory))
                print(f"  {directory}: {dir_stats['files']} files, {dir_stats['size_mb']} MB")
            print(f"  Total: {stats['network']['total_files']} files, {stats['network']['total_size_mb']} MB")
        else:
            print("  No network caches found")
        
    elif args.all:
        cleaner.clear_all_caches(force=args.force)
    elif args.joblib:
        cleaner.clear_joblib_cache(force=args.force)
    elif args.api:
        cleaner.clear_api_caches(force=args.force)
    elif args.network:
        cleaner.clear_network_caches(force=args.force)


if __name__ == "__main__":
    main()