import os
from pathlib import Path
from flask import Flask, jsonify, request
from config import Config
from app.database.db import init_app

def create_app(test_config=None) -> Flask:
    """
    Application factory for MediaGuard.
    Configures database teardown, session cookie security,
    OWASP security response headers, and safe error handling.
    """
    app = Flask(__name__, instance_relative_config=True)

    # Load default configuration
    app.config.from_object(Config)

    # Apply test or runtime overrides if provided
    if test_config:
        app.config.update(test_config)

    # Enforce Session Cookie Security
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
    if 'SESSION_COOKIE_SECURE' not in app.config:
        app.config['SESSION_COOKIE_SECURE'] = False  # True in production HTTPS

    # Ensure storage paths exist
    Path(app.config.get('ENCRYPTED_MEDIA_DIR', Config.ENCRYPTED_MEDIA_DIR)).mkdir(parents=True, exist_ok=True)
    Path(app.config.get('KEY_STORAGE_DIR', Config.KEY_STORAGE_DIR)).mkdir(parents=True, exist_ok=True)

    # Initialize Database connection & teardown handlers
    init_app(app)

    # Register Blueprints
    try:
        from app.routes.general import general_bp
        app.register_blueprint(general_bp)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from app.routes.media import media_bp
        app.register_blueprint(media_bp)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from app.routes.verify import verify_bp
        app.register_blueprint(verify_bp)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from app.routes.audit import audit_bp
        app.register_blueprint(audit_bp)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from app.routes.experiments import experiments_bp
        app.register_blueprint(experiments_bp)
    except (ImportError, ModuleNotFoundError):
        pass

    try:
        from app.routes.admin import admin_bp
        app.register_blueprint(admin_bp)
    except (ImportError, ModuleNotFoundError):
        pass

    # Security Headers Middleware
    @app.after_request
    def apply_security_headers(response):
        if app.config.get('SECURE_MODE', True):
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:;"
            )
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response

    # Safe Error Handlers (OWASP Top 10 Security Misconfiguration Prevention)
    @app.errorhandler(400)
    def bad_request(error):
        if app.config.get('SECURE_MODE', True):
            msg = getattr(error, 'description', 'Bad Request')
            return jsonify({'error': 'Bad Request', 'message': str(msg)}), 400
        return str(error), 400

    @app.errorhandler(401)
    def unauthorized(error):
        if app.config.get('SECURE_MODE', True):
            msg = getattr(error, 'description', 'Unauthorized')
            return jsonify({'error': 'Unauthorized', 'message': str(msg)}), 401
        return str(error), 401

    @app.errorhandler(403)
    def forbidden(error):
        if app.config.get('SECURE_MODE', True):
            msg = getattr(error, 'description', 'Forbidden')
            return jsonify({'error': 'Forbidden', 'message': str(msg)}), 403
        return str(error), 403

    @app.errorhandler(404)
    def not_found(error):
        if app.config.get('SECURE_MODE', True):
            msg = getattr(error, 'description', 'Not Found')
            return jsonify({'error': 'Not Found', 'message': str(msg)}), 404
        return str(error), 404

    @app.errorhandler(500)
    @app.errorhandler(Exception)
    def internal_error(error):
        if app.config.get('SECURE_MODE', True):
            # Suppress internal server stack traces to prevent credential/path leakage
            return jsonify({'error': 'Internal Server Error', 'message': 'An unexpected error occurred.'}), 500
        raise error

    return app
