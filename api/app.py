"""
Flask API Application for OMR Checker
Provides RESTful API endpoints for OMR sheet processing
"""

from flask import Flask
from flask_cors import CORS
import os
import sys

# Add parent directory to path to import OMRChecker modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.routes import api_blueprint


def create_app(config=None):
    """
    Application factory for Flask app

    Args:
        config: Optional configuration dictionary

    Returns:
        Flask application instance
    """
    app = Flask(__name__)

    # Default configuration
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'temp_uploads')
    app.config['JSON_SORT_KEYS'] = False

    # Apply custom config if provided
    if config:
        app.config.update(config)

    # Enable CORS for all routes
    CORS(app)

    # Create upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints
    app.register_blueprint(api_blueprint, url_prefix='/api')

    @app.route('/')
    def index():
        """Root endpoint with API information"""
        return {
            'name': 'OMR Checker API',
            'version': '1.0.0',
            'endpoints': {
                'POST /api/omr/process': 'Process single or multiple OMR images',
                'POST /api/omr/batch': 'Batch process multiple images',
                'POST /api/omr/validate-template': 'Validate template.json structure',
                'GET /api/health': 'Health check endpoint'
            }
        }

    @app.route('/api/health')
    def health():
        """Health check endpoint"""
        return {'status': 'healthy', 'service': 'OMR Checker API'}

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)
