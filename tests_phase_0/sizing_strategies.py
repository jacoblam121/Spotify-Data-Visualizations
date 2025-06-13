#!/usr/bin/env python3
"""
Sizing Strategies for Network Visualization
Implements three distinct approaches to artist node sizing.
"""

import math
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Tuple


def apply_glow_scaling(base_intensity: float, scaling_method: str, max_intensity: float = 1.0) -> float:
    """
    Apply configurable scaling to glow intensity.
    
    Args:
        base_intensity: Raw intensity value (0.0 to 1.0+)
        scaling_method: 'linear', 'sqrt', or 'squared'
        max_intensity: Maximum allowed intensity
        
    Returns:
        Scaled intensity clamped to [0.0, max_intensity]
    """
    if base_intensity <= 0:
        return 0.0
    
    if scaling_method == 'linear':
        scaled = base_intensity
    elif scaling_method == 'sqrt':
        scaled = base_intensity ** 0.5
    elif scaling_method == 'squared':
        scaled = base_intensity ** 2
    else:
        scaled = base_intensity  # Fallback to linear
    
    return max(0.0, min(max_intensity, scaled))


class SizingStrategy(ABC):
    """Abstract base class for node sizing strategies."""
    
    @abstractmethod
    def calculate(self, artist: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate size and glow metrics for an artist.
        
        Args:
            artist: Artist data including play counts, popularity, etc.
            context: Pre-calculated context (max values, user totals, etc.)
            
        Returns:
            Dict with 'size_score', 'glow_intensity', 'sizing_metric', 'sizing_value'
        """
        pass


class GlobalSizingStrategy(SizingStrategy):
    """
    Global Mode: Size based on worldwide popularity metrics.
    Uses Spotify popularity, followers, and Last.fm listeners.
    Glow emphasizes globally top artists.
    """
    
    def calculate(self, artist: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Get global metrics
        spotify_popularity = artist.get('spotify_popularity', 0)
        spotify_followers = artist.get('spotify_followers', 0)
        lastfm_listeners = artist.get('lastfm_listeners', 0)
        
        # Prioritize Spotify popularity (already logarithmically scaled by Spotify)
        if spotify_popularity > 0:
            primary_metric = spotify_popularity
            size_score = spotify_popularity / 100
            # Use exponential scaling to emphasize high-end differences
            size_score = size_score ** 2
            sizing_metric = 'spotify_popularity'
            sizing_value = spotify_popularity
        elif spotify_followers > 0:
            primary_metric = spotify_followers
            max_followers = context.get('max_spotify_followers', 1)
            min_followers = context.get('min_spotify_followers', 0)
            if max_followers > min_followers:
                size_score = (spotify_followers - min_followers) / (max_followers - min_followers)
                size_score = size_score ** 0.5  # Square root scaling for raw counts
            else:
                size_score = 0.5
            sizing_metric = 'spotify_followers'
            sizing_value = spotify_followers
        elif lastfm_listeners > 0:
            primary_metric = lastfm_listeners
            max_listeners = context.get('max_lastfm_listeners', 1)
            min_listeners = context.get('min_lastfm_listeners', 0)
            if max_listeners > min_listeners:
                size_score = (lastfm_listeners - min_listeners) / (max_listeners - min_listeners)
                size_score = size_score ** 0.5  # Square root scaling for raw counts
            else:
                size_score = 0.5
            sizing_metric = 'lastfm_listeners'
            sizing_value = lastfm_listeners
        else:
            # Fallback to play count
            play_count = artist.get('play_count', 0)
            max_plays = context.get('max_play_count', 1)
            size_score = play_count / max_plays if max_plays > 0 else 0.5
            size_score = size_score ** 0.5
            sizing_metric = 'play_count'
            sizing_value = play_count
        
        # Glow for user's most played artists (alternative perspective in global mode)
        glow_intensity = 0.0
        play_count = artist.get('play_count', 0)
        user_top_threshold = context.get('user_top_threshold', 0)
        if play_count >= user_top_threshold and user_top_threshold > 0:
            # Configurable percentage of user's library gets glow in global mode
            base_intensity = (play_count - user_top_threshold) / user_top_threshold
            scaling_method = context.get('glow_scaling_method', 'sqrt')
            max_glow = context.get('max_glow_intensity', 1.0)
            glow_intensity = apply_glow_scaling(base_intensity, scaling_method, max_glow)
        
        return {
            'size_score': max(0.0, min(1.0, size_score)),
            'glow_intensity': max(0.0, min(1.0, glow_intensity)),
            'sizing_metric': sizing_metric,
            'sizing_value': sizing_value
        }


class PersonalSizingStrategy(SizingStrategy):
    """
    Personal Mode: Size based on user's listening patterns.
    Uses play counts with logarithmic scaling.
    Glow emphasizes user's most-played artists.
    """
    
    def calculate(self, artist: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        play_count = artist.get('play_count', 0)
        max_log_plays = context.get('max_log_plays', 1)
        user_top_threshold = context.get('user_top_threshold', 0)
        
        # Logarithmic scaling for play counts
        log_plays = math.log(1 + play_count)
        size_score = log_plays / max_log_plays if max_log_plays > 0 else 0.5
        
        # Glow for globally popular artists (alternative perspective in personal mode)
        glow_intensity = 0.0
        spotify_popularity = artist.get('spotify_popularity', 0)
        popularity_threshold = context.get('personal_mode_threshold', 80)
        if spotify_popularity >= popularity_threshold:
            # Scale based on configurable threshold
            range_size = 100 - popularity_threshold
            base_intensity = (spotify_popularity - popularity_threshold) / range_size if range_size > 0 else 1.0
            scaling_method = context.get('glow_scaling_method', 'sqrt')
            max_glow = context.get('max_glow_intensity', 1.0)
            glow_intensity = apply_glow_scaling(base_intensity, scaling_method, max_glow)
        
        return {
            'size_score': max(0.0, min(1.0, size_score)),
            'glow_intensity': max(0.0, min(1.0, glow_intensity)),
            'sizing_metric': 'play_count',
            'sizing_value': play_count
        }


class AdaptiveSizingStrategy(SizingStrategy):
    """
    Adaptive/Hybrid Mode: Intelligently combines global and personal data.
    Uses dynamic weighting based on user data richness.
    Glow emphasizes "personal gems" - artists where user taste diverges from global consensus.
    """
    
    def calculate(self, artist: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        # Get both global and personal metrics
        spotify_popularity = artist.get('spotify_popularity', 0)
        play_count = artist.get('play_count', 0)
        
        # Calculate normalized scores
        global_score_norm = spotify_popularity / 100 if spotify_popularity > 0 else 0.0
        
        max_log_plays = context.get('max_log_plays', 1)
        log_plays = math.log(1 + play_count)
        personal_score_norm = log_plays / max_log_plays if max_log_plays > 0 else 0.0
        
        # Dynamic weighting based on user's total listening data
        total_user_plays = context.get('total_user_plays', 0)
        personal_weight = self._calculate_personal_weight(total_user_plays)
        global_weight = 1.0 - personal_weight
        
        # Weighted geometric mean for intuitive behavior
        # If either score is 0, result approaches 0
        epsilon = 0.01  # Prevent complete zeroing
        adjusted_personal = personal_score_norm + epsilon
        adjusted_global = global_score_norm + epsilon
        
        hybrid_score = (adjusted_personal ** personal_weight) * (adjusted_global ** global_weight)
        
        # Remove epsilon adjustment from final score
        hybrid_score = max(0.0, hybrid_score - epsilon)
        
        # "Personal Gems" glow - highlights where personal taste diverges from global
        glow_intensity = 0.0
        ratio_threshold = context.get('adaptive_mode_ratio', 2.0)
        
        if global_score_norm > 0.1:  # Only for artists with some global presence
            divergence_ratio = personal_score_norm / (global_score_norm + 0.01)
            # Glow when personal significance significantly exceeds global
            if divergence_ratio > ratio_threshold:
                # Dynamic scaling based on threshold - larger threshold = more gradual scaling
                scale_factor = 3.0 if ratio_threshold <= 2.0 else ratio_threshold * 1.5
                base_intensity = (divergence_ratio - ratio_threshold) / scale_factor
                scaling_method = context.get('glow_scaling_method', 'sqrt')
                max_glow = context.get('max_glow_intensity', 1.0)
                glow_intensity = apply_glow_scaling(base_intensity, scaling_method, max_glow)
        elif personal_score_norm > 0.3:  # High personal score for unknown artist
            scaling_method = context.get('glow_scaling_method', 'sqrt')
            max_glow = context.get('max_glow_intensity', 1.0)
            glow_intensity = apply_glow_scaling(personal_score_norm, scaling_method, max_glow)
        
        # Determine primary metric for display
        if personal_weight > 0.5:
            sizing_metric = 'hybrid_personal_emphasis'
            sizing_value = f"Personal: {play_count}, Global: {spotify_popularity}"
        else:
            sizing_metric = 'hybrid_global_emphasis'
            sizing_value = f"Global: {spotify_popularity}, Personal: {play_count}"
        
        return {
            'size_score': max(0.0, min(1.0, hybrid_score)),
            'glow_intensity': max(0.0, min(1.0, glow_intensity)),
            'sizing_metric': sizing_metric,
            'sizing_value': sizing_value,
            'personal_weight': personal_weight,
            'global_weight': global_weight
        }
    
    def _calculate_personal_weight(self, total_plays: int) -> float:
        """
        Calculate dynamic weighting based on user's data richness.
        Uses sigmoid function for smooth transition.
        
        Args:
            total_plays: User's total play count across all artists
            
        Returns:
            Weight for personal data (0.0 to 1.0)
        """
        # Sigmoid parameters
        k = 0.001  # Steepness of curve
        x0 = 5000  # Play count for 50% personal weight
        
        # Sigmoid function: more plays = higher personal weight
        weight = 1 / (1 + math.exp(-k * (total_plays - x0)))
        
        # Ensure minimum personal influence (25%) and maximum (85%)
        return max(0.25, min(0.85, weight))


class SizingStrategyFactory:
    """Factory for creating sizing strategy instances."""
    
    @staticmethod
    def create(mode: str) -> SizingStrategy:
        """
        Create sizing strategy based on mode.
        
        Args:
            mode: 'global', 'personal', or 'adaptive'
            
        Returns:
            Appropriate sizing strategy instance
        """
        if mode.lower() == 'global':
            return GlobalSizingStrategy()
        elif mode.lower() == 'personal':
            return PersonalSizingStrategy()
        elif mode.lower() in ['adaptive', 'hybrid']:
            return AdaptiveSizingStrategy()
        else:
            raise ValueError(f"Unknown sizing mode: {mode}")


def calculate_context(artists: List[Dict[str, Any]], config=None) -> Dict[str, Any]:
    """
    Calculate context metrics needed for all sizing strategies.
    
    Args:
        artists: List of artist data dictionaries
        
    Returns:
        Context dictionary with max values, thresholds, etc.
    """
    if not artists:
        return {}
    
    # Calculate global metrics
    spotify_followers = [a.get('spotify_followers', 0) for a in artists]
    lastfm_listeners = [a.get('lastfm_listeners', 0) for a in artists]
    play_counts = [a.get('play_count', 0) for a in artists]
    
    # Calculate logarithmic scaling for personal data
    log_plays = [math.log(1 + pc) for pc in play_counts]
    max_log_plays = max(log_plays) if log_plays else 1
    
    # User data richness
    total_user_plays = sum(play_counts)
    
    # Configurable percentage threshold for user's library
    glow_percentage = 0.15  # Default 15%
    if config:
        try:
            glow_percentage = config.get_float('GlowEffects', 'GLOBAL_MODE_GLOW_PERCENTAGE', fallback=0.15)
        except:
            glow_percentage = 0.15
    
    sorted_plays = sorted(play_counts, reverse=True)
    top_percent_index = max(0, int(len(sorted_plays) * glow_percentage))
    user_top_threshold = sorted_plays[top_percent_index] if sorted_plays else 0
    
    # Load glow configuration
    personal_threshold = 80
    adaptive_ratio = 2.0
    scaling_method = 'sqrt'
    max_glow = 1.0
    
    if config:
        try:
            personal_threshold = config.get_int('GlowEffects', 'PERSONAL_MODE_POPULARITY_THRESHOLD', fallback=80)
            adaptive_ratio = config.get_float('GlowEffects', 'ADAPTIVE_MODE_RATIO_THRESHOLD', fallback=2.0)
            scaling_method = config.get('GlowEffects', 'GLOW_SCALING_METHOD', fallback='sqrt')
            max_glow = config.get_float('GlowEffects', 'MAX_GLOW_INTENSITY', fallback=1.0)
        except:
            pass
    
    return {
        'max_spotify_followers': max(spotify_followers) if spotify_followers else 1,
        'min_spotify_followers': min(f for f in spotify_followers if f > 0) if spotify_followers else 0,
        'max_lastfm_listeners': max(lastfm_listeners) if lastfm_listeners else 1,
        'min_lastfm_listeners': min(l for l in lastfm_listeners if l > 0) if lastfm_listeners else 0,
        'max_play_count': max(play_counts) if play_counts else 1,
        'max_log_plays': max_log_plays,
        'total_user_plays': total_user_plays,
        'user_top_threshold': user_top_threshold,
        
        # Glow configuration
        'glow_percentage': glow_percentage,
        'personal_mode_threshold': personal_threshold,
        'adaptive_mode_ratio': adaptive_ratio,
        'glow_scaling_method': scaling_method,
        'max_glow_intensity': max_glow
    }