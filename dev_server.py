#!/usr/bin/env python3
"""
Modern Flask Development Server
Solves browser caching and CORS issues with proper HTTP headers
"""

import os
import sys
import socket
import re
from flask import Flask, send_from_directory, request, jsonify
from flask_cors import CORS
from werkzeug.serving import WSGIRequestHandler
import logging

# Import album_art_utils at module level for better performance
try:
    import album_art_utils
    from config_loader import AppConfig
    ALBUM_ART_AVAILABLE = True
except ImportError:
    ALBUM_ART_AVAILABLE = False
    print("⚠️ album_art_utils not available - artist photo caching disabled")

class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for better readability"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green  
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'      # Reset
    }
    
    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)

def find_free_port(start_port=8000):
    """Find a free port starting from start_port"""
    for port in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    
    # Enable CORS for all domains and all routes
    CORS(app, resources={
        r"/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    @app.after_request
    def add_development_headers(response):
        """Add headers to prevent caching and enable debugging"""
        # Prevent all caching during development
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Security headers for development
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Debug information
        response.headers['X-Dev-Server'] = 'Flask-Development-Server'
        
        return response
    
    @app.route('/')
    def index():
        """Serve the main page"""
        return send_from_directory(app.static_folder, 'network_enhanced.html')
    
    @app.route('/test')
    def test_page():
        """Serve the test page"""
        return send_from_directory(app.static_folder, 'test_phase2_1_simple.html')
    
    @app.route('/static/artist_art_cache/<filename>')
    def serve_artist_art(filename):
        """
        Serve artist profile photos from artist_art_cache directory.
        If image is missing, automatically fetch from Spotify API and cache it.
        """
        if not ALBUM_ART_AVAILABLE:
            return jsonify({'error': 'Artist photo caching not available'}), 503
            
        try:
            # Try to serve existing cached file first
            return send_from_directory('artist_art_cache', filename)
        except FileNotFoundError:
            # Image not cached - fetch fresh from Spotify API
            app.logger.info(f"🔄 Cache miss for {filename}, fetching from Spotify API...")
            
            # Extract artist name from filename pattern: "artist_ArtistName_artist.jpg"
            if not filename.startswith('artist_') or not filename.endswith('_artist.jpg'):
                app.logger.warning(f"⚠️ Invalid filename pattern: {filename}")
                return jsonify({'error': f'Invalid artist photo filename: {filename}'}), 404
            
            # Extract artist name: "artist_Taylor Swift_artist.jpg" -> "Taylor Swift"
            artist_name = filename[7:-11]  # Remove "artist_" prefix and "_artist.jpg" suffix
            artist_name = artist_name.replace('_', ' ')  # Convert underscores back to spaces
            
            # Security: Sanitize artist name to prevent path traversal and injection attacks
            artist_name = re.sub(r'[^\w\s-]', '', artist_name).strip()[:100]  # Allow only alphanumeric, spaces, hyphens
            # Additional security: block any remaining path traversal attempts
            if not artist_name or len(artist_name) < 1 or '..' in artist_name or '/' in artist_name:
                app.logger.warning(f"⚠️ Invalid artist name after sanitization: {filename}")
                return jsonify({'error': f'Invalid artist name in filename: {filename}'}), 404
            
            app.logger.info(f"🎵 Extracted artist name: '{artist_name}'")
            
            try:
                # Initialize album_art_utils if needed
                config = AppConfig()
                album_art_utils.initialize_from_config(config)
                
                # Fetch and cache the artist photo
                photo_path = album_art_utils.get_artist_photo_path(artist_name)
                if photo_path:
                    app.logger.info(f"✅ Successfully fetched and cached: {photo_path}")
                    # Now serve the freshly cached image
                    return send_from_directory('artist_art_cache', filename)
                else:
                    app.logger.warning(f"❌ No photo available for artist: {artist_name}")
                    return jsonify({'error': f'No photo available for artist: {artist_name}'}), 404
                    
            except Exception as e:
                app.logger.error(f"💥 Error fetching artist photo for '{artist_name}': {e}")
                return jsonify({'error': f'Failed to fetch photo for {artist_name}: {str(e)}'}), 500
    
    @app.route('/health')
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'server': 'Flask Development Server',
            'static_folder': app.static_folder,
            'routes': [str(rule) for rule in app.url_map.iter_rules()]
        })
    
    @app.errorhandler(404)
    def not_found(error):
        """Custom 404 handler with helpful information"""
        return jsonify({
            'error': 'File not found',
            'path': request.path,
            'available_routes': [str(rule) for rule in app.url_map.iter_rules()],
            'static_folder': app.static_folder
        }), 404
    
    # Log all requests for debugging
    @app.before_request
    def log_request_info():
        app.logger.info(f'{request.method} {request.path} - {request.remote_addr}')
    
    return app

def setup_logging():
    """Setup colored logging for better development experience"""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with color formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    formatter = ColoredFormatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def main():
    """Main entry point"""
    logger = setup_logging()
    
    # Use fixed port for development predictability, but allow override
    port = int(os.environ.get('PORT', 8000))
    
    # If the default port is taken, find a free one
    if port == 8000:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
        except OSError:
            logger.warning(f"⚠️  Port {port} is in use, finding alternative...")
            port = find_free_port(8001)
            if port is None:
                logger.error("❌ No free ports found between 8001-8019")
                return 1
    
    # Get working directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    app = create_app()
    
    # Configure Flask logging
    app.logger.setLevel(logging.INFO)
    
    logger.info("🚀 Starting Flask Development Server")
    logger.info(f"📁 Serving from: {project_root}")
    logger.info(f"🌐 Server starting on port {port}")
    logger.info(f"📱 Main app: http://localhost:{port}/")
    logger.info(f"🧪 Test page: http://localhost:{port}/test")
    logger.info(f"💚 Health check: http://localhost:{port}/health")
    logger.info(f"📁 Static files: http://localhost:{port}/static/")
    logger.info(f"🛑 Press Ctrl+C to stop")
    
    try:
        # Custom request handler to reduce noise
        class QuietRequestHandler(WSGIRequestHandler):
            def log_request(self, code='-', size='-'):
                # Only log errors, not every request
                if str(code).startswith('4') or str(code).startswith('5'):
                    super().log_request(code, size)
        
        app.run(
            host='127.0.0.1',
            port=port,
            debug=True,
            use_reloader=True,
            use_debugger=True,
            request_handler=QuietRequestHandler
        )
        
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
        return 0
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())