import pytest
from flask import Flask, abort
from app import create_app

def test_app_factory_creates_app():
    """Verify create_app loads configuration properly."""
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-secret'})
    assert isinstance(app, Flask)
    assert app.config['TESTING'] is True
    assert app.config['SESSION_COOKIE_HTTPONLY'] is True
    assert app.config['SESSION_COOKIE_SAMESITE'] == 'Strict'

def test_security_headers_present_on_response():
    """Verify that all required OWASP security headers are present in responses."""
    app = create_app({'TESTING': True, 'SECURE_MODE': True})
    
    @app.route('/test-headers')
    def dummy_route():
        return "OK"

    client = app.test_client()
    response = client.get('/test-headers')
    assert response.status_code == 200

    headers = response.headers
    assert "default-src 'self'" in headers.get('Content-Security-Policy', '')
    assert headers.get('X-Frame-Options') == 'DENY'
    assert headers.get('X-Content-Type-Options') == 'nosniff'
    assert headers.get('X-XSS-Protection') == '1; mode=block'
    assert headers.get('Strict-Transport-Security') == 'max-age=31536000; includeSubDomains'

def test_security_headers_insecure_mode_omits_or_loosens_hsts():
    """Verify that when SECURE_MODE is False (demonstrating OWASP dual-mode), HSTS is disabled."""
    app = create_app({'TESTING': True, 'SECURE_MODE': False})
    
    @app.route('/test-headers-insecure')
    def dummy_route():
        return "OK"

    client = app.test_client()
    response = client.get('/test-headers-insecure')
    assert response.status_code == 200
    assert 'Strict-Transport-Security' not in response.headers

def test_generic_error_handlers():
    """Verify that custom error handlers (400, 403, 404, 500) return safe error responses without leaking tracebacks."""
    app = create_app({'TESTING': True, 'SECURE_MODE': True})

    @app.route('/trigger-400')
    def trigger_400():
        abort(400)

    @app.route('/trigger-403')
    def trigger_403():
        abort(403)

    @app.route('/trigger-500')
    def trigger_500():
        raise RuntimeError("Internal database connection failed with secret credentials leaked!")

    client = app.test_client()

    # 404 Not Found
    res_404 = client.get('/nonexistent-route-xyz')
    assert res_404.status_code == 404
    assert res_404.is_json
    assert "error" in res_404.get_json()

    # 400 Bad Request
    res_400 = client.get('/trigger-400')
    assert res_400.status_code == 400
    assert res_400.is_json
    assert "error" in res_400.get_json()

    # 403 Forbidden
    res_403 = client.get('/trigger-403')
    assert res_403.status_code == 403
    assert res_403.is_json
    assert "error" in res_403.get_json()

    # 500 Internal Server Error (trap sensitive traceback)
    res_500 = client.get('/trigger-500')
    assert res_500.status_code == 500
    assert res_500.is_json
    body = res_500.get_json()
    assert "secret credentials" not in str(body)
    assert body.get("error") == "Internal Server Error"
