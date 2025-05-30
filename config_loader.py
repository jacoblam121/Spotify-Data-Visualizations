# config_loader.py
import configparser
import os

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
        print(f"Non-existent key (with fallback): {config.get('General', 'NON_EXISTENT_KEY', 'fallback_value')}")
        print(f"Non-existent bool (with fallback): {config.get_bool('General', 'NON_EXISTENT_BOOL', True)}")

    except FileNotFoundError as e:
        print(e)
    except Exception as e:
        print(f"An error occurred: {e}")