# config_loader.py
import configparser
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class AppConfig:
    def __init__(self, filepath="configurations.txt"):
        self.config = configparser.ConfigParser()
        # Preserve case of keys
        self.config.optionxform = str

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
        self.config.read(filepath)

    def get(self, section, key, fallback=None):
        return self.config.get(section, key, fallback=fallback)

    def get_int(self, section, key, fallback=0):
        try:
            return self.config.getint(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError, ValueError):
            return fallback

    def get_float(self, section, key, fallback=0.0):
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError, ValueError):
            return fallback

    def get_bool(self, section, key, fallback=False):
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoOptionError, configparser.NoSectionError, ValueError):
            return fallback
    
    def get_list(self, section, key, fallback=None, delimiter=','):
        if fallback is None:
            fallback = []
        try:
            value_str = self.config.get(section, key)
            if not value_str: # Handle empty string
                return fallback
            return [item.strip() for item in value_str.split(delimiter)]
        except (configparser.NoOptionError, configparser.NoSectionError):
            return fallback
    
    def get_lastfm_config(self):
        """Get Last.fm API configuration with .env override support."""
        # Check environment variables first, fallback to config file
        api_key = os.getenv('LASTFM_API_KEY') or self.get('LastfmAPI', 'API_KEY', '')
        api_secret = os.getenv('LASTFM_API_SECRET') or self.get('LastfmAPI', 'API_SECRET', '')
        
        return {
            'api_key': api_key,
            'api_secret': api_secret,
            'enabled': self.get_bool('LastfmAPI', 'ENABLE_LASTFM', False),
            'limit': self.get_int('LastfmAPI', 'SIMILAR_ARTISTS_LIMIT', 100),
            'cache_dir': self.get('LastfmAPI', 'CACHE_DIR', 'lastfm_cache'),
            'cache_expiry_days': self.get_int('LastfmAPI', 'CACHE_EXPIRY_DAYS', 30)
        }
    
    def get_spotify_config(self):
        """Get Spotify API configuration with .env override support."""
        # Check environment variables first, fallback to config file
        client_id = os.getenv('SPOTIFY_CLIENT_ID') or self.get('AlbumArtSpotify', 'SPOTIFY_CLIENT_ID', '')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET') or self.get('AlbumArtSpotify', 'SPOTIFY_CLIENT_SECRET', '')
        
        return {
            'client_id': client_id,
            'client_secret': client_secret,
            'art_cache_dir': self.get('AlbumArtSpotify', 'ART_CACHE_DIR', 'album_art_cache'),
            'artist_art_cache_dir': self.get('AlbumArtSpotify', 'ARTIST_ART_CACHE_DIR', 'artist_art_cache'),
            'negative_cache_hours': self.get_int('AlbumArtSpotify', 'NEGATIVE_CACHE_HOURS', 24)
        }
    
    def get_musicbrainz_config(self):
        """Get MusicBrainz API configuration."""
        return {
            'enabled': self.get_bool('MusicBrainzAPI', 'ENABLE_MUSICBRAINZ', True),
            'user_agent': self.get('General', 'USER_AGENT', 'SpotifyRaceChart/1.0'),
            'cache_dir': self.get('MusicBrainzAPI', 'CACHE_DIR', 'musicbrainz_cache'),
            'cache_expiry_days': self.get_int('MusicBrainzAPI', 'CACHE_EXPIRY_DAYS', 30)
        }
    
    def get_network_visualization_config(self):
        """Get network visualization configuration."""
        sizing_strategy = self.get('NetworkVisualization', 'NODE_SIZING_STRATEGY', 'hybrid_multiply').lower().strip()
        fallback_behavior = self.get('NetworkVisualization', 'FALLBACK_BEHAVIOR', 'fallback').lower().strip()
        
        # Validate node sizing strategy
        valid_strategies = ['lastfm', 'spotify_popularity', 'hybrid_multiply', 'hybrid_weighted']
        if sizing_strategy not in valid_strategies:
            print(f"Warning: Invalid NODE_SIZING_STRATEGY '{sizing_strategy}'. Valid options: {valid_strategies}")
            print("Defaulting to 'hybrid_multiply'.")
            sizing_strategy = 'hybrid_multiply'
        
        # Validate fallback behavior
        valid_fallbacks = ['fallback', 'skip', 'default']
        if fallback_behavior not in valid_fallbacks:
            print(f"Warning: Invalid FALLBACK_BEHAVIOR '{fallback_behavior}'. Valid options: {valid_fallbacks}")
            print("Defaulting to 'fallback'.")
            fallback_behavior = 'fallback'
        
        return {
            'node_sizing_strategy': sizing_strategy,
            'fetch_both_sources': self.get_bool('NetworkVisualization', 'FETCH_BOTH_SOURCES', True),
            'fallback_behavior': fallback_behavior,
            'spotify_popularity_boost': self.get_float('NetworkVisualization', 'SPOTIFY_POPULARITY_BOOST', 1.5),
            'top_n_artists': self.get_int('NetworkVisualization', 'TOP_N_ARTISTS', 100),
            'min_similarity_threshold': self.get_float('NetworkVisualization', 'MIN_SIMILARITY_THRESHOLD', 0.2),
            'min_plays_threshold': self.get_int('NetworkVisualization', 'MIN_PLAYS_THRESHOLD', 5),
            'enable_secondary_genres': self.get_bool('NetworkVisualization', 'ENABLE_SECONDARY_GENRES', True)
        }

    def validate_visualization_mode(self):
        """Validate the visualization mode setting and return the normalized mode."""
        mode = self.get('VisualizationMode', 'MODE', 'tracks').lower().strip()
        valid_modes = ['tracks', 'artists']
        
        if mode not in valid_modes:
            print(f"Warning: Invalid visualization mode '{mode}'. Valid modes are: {valid_modes}")
            print("Defaulting to 'tracks' mode.")
            return 'tracks'
        
        return mode

# Global config instance (optional, but can be convenient)
# app_config = None

# def load_app_config(filepath="configurations.txt"):
#     global app_config
#     if app_config is None:
#         app_config = AppConfig(filepath)
#     return app_config

if __name__ == '__main__':
    # Test loading
    try:
        config = AppConfig() # Assumes configurations.txt is in the same directory
        print("Configuration loaded successfully.")
        print(f"User Agent: {config.get('General', 'USER_AGENT', 'DefaultAgent/1.0')}")
        print(f"Data Source: {config.get('DataSource', 'SOURCE', 'lastfm')}")
        print(f"Target FPS: {config.get_int('AnimationOutput', 'TARGET_FPS', 25)}")
        print(f"Use NVENC: {config.get_bool('AnimationOutput', 'USE_NVENC_IF_AVAILABLE', False)}")
        print(f"Preferred Fonts: {config.get_list('FontPreferences', 'PREFERRED_FONTS')}")
        print(f"Visualization Mode: {config.validate_visualization_mode()}")
        print(f"Non-existent key (with fallback): {config.get('General', 'NON_EXISTENT_KEY', 'fallback_value')}")
        print(f"Non-existent bool (with fallback): {config.get_bool('General', 'NON_EXISTENT_BOOL', True)}")

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")