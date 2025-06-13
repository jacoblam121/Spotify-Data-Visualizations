#!/usr/bin/env python3
"""
Node Sizing Calculator
Calculates node sizes for network visualization using various hybrid approaches
combining Last.fm listeners and Spotify popularity.
"""

import math
from typing import Dict, Optional

class NodeSizingCalculator:
    """Calculator for determining node sizes using hybrid approaches."""
    
    def __init__(self, config: Dict):
        """
        Initialize calculator with configuration.
        
        Args:
            config: Network visualization config from AppConfig
        """
        self.strategy = config.get('node_sizing_strategy', 'hybrid_multiply')
        self.spotify_boost = config.get('spotify_popularity_boost', 1.5)
        self.fallback_behavior = config.get('fallback_behavior', 'fallback')
    
    def calculate_node_size(self, artist_data: Dict, user_play_count: int = 0) -> Dict:
        """
        Calculate node size based on configured strategy.
        
        Args:
            artist_data: Result from EnhancedArtistDataFetcher.fetch_artist_data()
            user_play_count: User's play count for this artist (for fallback)
            
        Returns:
            Dictionary with sizing information:
            {
                'size': int,           # Primary size value for visualization
                'strategy_used': str,  # Which strategy was actually used
                'components': dict,    # Breakdown of components used
                'display_text': str    # Human-readable description
            }
        """
        lastfm_data = artist_data.get('lastfm_data')
        spotify_data = artist_data.get('spotify_data')
        
        # Extract base values
        lastfm_listeners = lastfm_data.get('listeners', 0) if lastfm_data else 0
        spotify_popularity = spotify_data.get('popularity', 0) if spotify_data else 0
        spotify_followers = spotify_data.get('followers', 0) if spotify_data else 0
        
        result = {
            'size': 0,
            'strategy_used': self.strategy,
            'components': {
                'lastfm_listeners': lastfm_listeners,
                'spotify_popularity': spotify_popularity,
                'spotify_followers': spotify_followers,
                'user_play_count': user_play_count
            },
            'display_text': ''
        }
        
        # Apply sizing strategy
        if self.strategy == 'lastfm':
            result['size'] = lastfm_listeners
            result['display_text'] = f"{lastfm_listeners:,} Last.fm listeners"
            
        elif self.strategy == 'spotify_popularity':
            # Scale popularity (0-100) to reasonable size range
            result['size'] = spotify_popularity * 10000
            result['display_text'] = f"{spotify_popularity}/100 Spotify popularity"
            
        elif self.strategy == 'hybrid_multiply':
            if lastfm_listeners > 0:
                # Use Last.fm as base, multiply by normalized Spotify popularity boost
                popularity_multiplier = 1 + ((spotify_popularity / 100) * (self.spotify_boost - 1))
                result['size'] = int(lastfm_listeners * popularity_multiplier)
                result['display_text'] = f"{lastfm_listeners:,} × {popularity_multiplier:.2f} (pop boost)"
            else:
                # Fallback to pure Spotify popularity
                result['size'] = spotify_popularity * 10000
                result['display_text'] = f"{spotify_popularity}/100 Spotify popularity (fallback)"
                result['strategy_used'] = 'spotify_popularity_fallback'
                
        elif self.strategy == 'hybrid_weighted':
            # Weighted combination: 70% Last.fm, 30% scaled Spotify popularity
            lastfm_component = lastfm_listeners * 0.7
            spotify_component = spotify_popularity * 50000 * 0.3
            result['size'] = int(lastfm_component + spotify_component)
            result['display_text'] = f"{lastfm_listeners:,} + pop({spotify_popularity}) weighted"
        
        # Apply fallback if primary strategy failed
        if result['size'] == 0:
            result = self._apply_fallback(result, user_play_count)
        
        # Ensure minimum size for visualization
        result['size'] = max(result['size'], 1000)
        
        return result
    
    def _apply_fallback(self, result: Dict, user_play_count: int) -> Dict:
        """Apply fallback sizing when primary strategy fails."""
        if self.fallback_behavior == 'default':
            # Use user play count scaled up
            result['size'] = max(user_play_count * 1000, 1000)
            result['strategy_used'] = 'play_count_fallback'
            result['display_text'] = f"{user_play_count} plays (fallback)"
            
        elif self.fallback_behavior == 'skip':
            # Keep size as 0 to indicate this node should be excluded
            result['size'] = 0
            result['strategy_used'] = 'excluded'
            result['display_text'] = "Excluded (no data)"
            
        else:  # fallback behavior
            # Try alternative data sources
            components = result['components']
            
            if components['spotify_followers'] > 0:
                result['size'] = components['spotify_followers']
                result['strategy_used'] = 'spotify_followers_fallback'
                result['display_text'] = f"{components['spotify_followers']:,} Spotify followers (fallback)"
                
            elif components['spotify_popularity'] > 0:
                result['size'] = components['spotify_popularity'] * 10000
                result['strategy_used'] = 'spotify_popularity_fallback'
                result['display_text'] = f"{components['spotify_popularity']}/100 Spotify popularity (fallback)"
                
            elif components['lastfm_listeners'] > 0:
                result['size'] = components['lastfm_listeners']
                result['strategy_used'] = 'lastfm_fallback'
                result['display_text'] = f"{components['lastfm_listeners']:,} Last.fm listeners (fallback)"
                
            else:
                # Final fallback to play count
                result['size'] = max(user_play_count * 1000, 1000)
                result['strategy_used'] = 'play_count_final_fallback'
                result['display_text'] = f"{user_play_count} plays (final fallback)"
        
        return result
    
    def calculate_batch_sizes(self, artist_data_list: list, play_counts: Dict[str, int] = None) -> list:
        """
        Calculate sizes for multiple artists.
        
        Args:
            artist_data_list: List of artist data from EnhancedArtistDataFetcher
            play_counts: Dict mapping artist names to play counts
            
        Returns:
            List of sizing results
        """
        if play_counts is None:
            play_counts = {}
        
        results = []
        for artist_data in artist_data_list:
            artist_name = artist_data.get('artist_name', '')
            user_plays = play_counts.get(artist_name, 0)
            
            size_result = self.calculate_node_size(artist_data, user_plays)
            size_result['artist_name'] = artist_name
            size_result['canonical_name'] = artist_data.get('canonical_name', artist_name)
            
            results.append(size_result)
        
        return results
    
    def get_sizing_statistics(self, sizing_results: list) -> Dict:
        """
        Get statistics about the sizing results.
        
        Args:
            sizing_results: List of results from calculate_batch_sizes()
            
        Returns:
            Statistics dictionary
        """
        if not sizing_results:
            return {}
        
        sizes = [r['size'] for r in sizing_results if r['size'] > 0]
        strategies_used = [r['strategy_used'] for r in sizing_results]
        
        # Count strategy usage
        strategy_counts = {}
        for strategy in strategies_used:
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        return {
            'total_artists': len(sizing_results),
            'artists_with_size': len(sizes),
            'min_size': min(sizes) if sizes else 0,
            'max_size': max(sizes) if sizes else 0,
            'avg_size': sum(sizes) / len(sizes) if sizes else 0,
            'median_size': sorted(sizes)[len(sizes) // 2] if sizes else 0,
            'strategy_usage': strategy_counts,
            'size_range_ratio': max(sizes) / min(sizes) if sizes and min(sizes) > 0 else 0
        }


def test_node_sizing_calculator():
    """Test the node sizing calculator with sample data."""
    print("🧪 Testing Node Sizing Calculator")
    print("=" * 50)
    
    # Sample configuration
    config = {
        'node_sizing_strategy': 'hybrid_multiply',
        'spotify_popularity_boost': 1.5,
        'fallback_behavior': 'fallback'
    }
    
    calculator = NodeSizingCalculator(config)
    
    # Sample artist data (simulating different scenarios)
    test_data = [
        {
            'artist_name': 'Taylor Swift',
            'canonical_name': 'Taylor Swift',
            'lastfm_data': {'listeners': 5160232},
            'spotify_data': {'popularity': 95, 'followers': 85000000}
        },
        {
            'artist_name': 'ive',
            'canonical_name': 'Ive',
            'lastfm_data': {'listeners': 837966},
            'spotify_data': {'popularity': 88, 'followers': 12000000}
        },
        {
            'artist_name': 'Unknown Artist',
            'canonical_name': 'Unknown Artist',
            'lastfm_data': None,
            'spotify_data': None
        },
        {
            'artist_name': 'Spotify Only',
            'canonical_name': 'Spotify Only',
            'lastfm_data': None,
            'spotify_data': {'popularity': 75, 'followers': 5000000}
        }
    ]
    
    play_counts = {
        'Taylor Swift': 1500,
        'ive': 800,
        'Unknown Artist': 50,
        'Spotify Only': 200
    }
    
    # Test different strategies
    strategies = ['lastfm', 'spotify_popularity', 'hybrid_multiply', 'hybrid_weighted']
    
    for strategy in strategies:
        print(f"\n📊 Testing strategy: {strategy}")
        print("-" * 40)
        
        config['node_sizing_strategy'] = strategy
        calc = NodeSizingCalculator(config)
        
        results = calc.calculate_batch_sizes(test_data, play_counts)
        
        for result in results:
            name = result['artist_name'][:15]
            size = result['size']
            display = result['display_text']
            print(f"  {name:<15} {size:>10,} - {display}")
        
        # Show statistics
        stats = calc.get_sizing_statistics(results)
        print(f"  Range: {stats['min_size']:,} - {stats['max_size']:,} (ratio: {stats['size_range_ratio']:.1f}x)")
        print(f"  Strategies used: {', '.join(stats['strategy_usage'].keys())}")


if __name__ == "__main__":
    test_node_sizing_calculator()