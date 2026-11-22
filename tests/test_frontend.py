import re
from pathlib import Path
import pytest
from app import create_app

def test_home_page_renders_html_with_design_tokens(client):
    """Verify public home page renders semantic HTML5 and links to CSS tokens."""
    response = client.get('/')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'MediaGuard' in html
    assert 'Cryptographic Provenance' in html
    assert '/static/css/variables.css' in html
    assert '/static/css/style.css' in html
    assert '/verify' in html
    assert 'CS-353 Information Security · NUST SEECS' in html

def test_login_page_renders_clean_form(client):
    """Verify /auth/login renders the glass card login form with TOTP input."""
    response = client.get('/auth/login')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'MediaGuard Vault Access' in html
    assert 'name="username"' in html
    assert 'name="password"' in html
    assert 'name="totp_code"' in html
    assert 'Authenticate & Unlock Vault' in html
    assert 'card-glass' in html

def test_register_page_renders_form_and_security_info(client):
    """Verify /auth/register renders registration form with key generation explanation."""
    response = client.get('/auth/register')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'MediaGuard Registration' in html
    assert 'name="username"' in html
    assert 'name="email"' in html
    assert 'name="password"' in html
    assert 'name="confirm_password"' in html
    assert 'Zero-Plaintext Security' in html
    assert '2048-bit RSA-PSS' in html

def test_setup_2fa_page_renders_qr_and_input(client):
    """Verify /auth/setup-2fa renders QR code container and 6-digit confirmation code input."""
    response = client.get('/auth/setup-2fa')
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'Activate Authenticator App' in html
    assert '/auth/totp-qr' in html
    assert 'name="code"' in html
    assert 'Verify & Activate Account' in html

def test_zero_inline_styles_in_all_templates():
    """Strictly verify that style="..." inline styles do NOT exist in any HTML template."""
    template_dir = Path(__file__).resolve().parent.parent / 'app' / 'templates'
    html_files = list(template_dir.glob('**/*.html'))
    assert len(html_files) >= 4, "Expected at least base, index, login, register, setup_2fa templates"

    for template_path in html_files:
        content = template_path.read_text(encoding='utf-8')
        # Check for style= attribute (case-insensitive)
        inline_style_matches = re.findall(r'style\s*=\s*["\'][^"\']*["\']', content, re.IGNORECASE)
        assert not inline_style_matches, (
            f"Vibecoding violation in {template_path.name}: "
            f"Found forbidden inline style(s): {inline_style_matches}"
        )

def test_css_variables_contain_all_design_tokens():
    """Verify variables.css defines all required design system variables."""
    css_path = Path(__file__).resolve().parent.parent / 'app' / 'static' / 'css' / 'variables.css'
    assert css_path.exists(), "variables.css must exist"
    content = css_path.read_text(encoding='utf-8')

    required_tokens = [
        '--bg-base', '--bg-surface', '--bg-elevated', '--bg-card',
        '--border-subtle', '--border-default', '--border-focus',
        '--primary', '--primary-hover', '--primary-glow',
        '--success', '--success-bg', '--success-border',
        '--danger', '--danger-bg', '--danger-border',
        '--warning', '--warning-bg', '--warning-border',
        '--info', '--info-bg', '--info-border',
        '--text-main', '--text-muted', '--text-dim',
        '--font-sans', '--font-mono',
        '--radius-sm', '--radius-md', '--radius-lg',
        '--shadow-sm', '--shadow-md', '--shadow-lg'
    ]

    for token in required_tokens:
        assert token in content, f"variables.css missing required design token: {token}"

def test_style_css_contains_all_component_classes():
    """Verify style.css implements all standardized component classes."""
    style_path = Path(__file__).resolve().parent.parent / 'app' / 'static' / 'css' / 'style.css'
    assert style_path.exists(), "style.css must exist"
    content = style_path.read_text(encoding='utf-8')

    required_classes = [
        '.card-glass', '.btn', '.btn-primary', '.btn-secondary', '.btn-danger', '.btn-outline',
        '.badge-status', '.badge-authentic', '.badge-modified', '.badge-warning', '.badge-info', '.badge-role',
        '.input-terminal', '.table-vault', '.nav-bar', '.nav-link', '.nav-brand',
        '.alert-success', '.alert-danger', '.alert-warning', '.alert-info',
        '.font-mono', '.hash-badge', '.dropzone'
    ]

    for cls in required_classes:
        assert cls in content, f"style.css missing required component class: {cls}"

def test_main_js_exists_and_contains_event_handlers():
    """Verify main.js exists and implements required client utilities."""
    js_path = Path(__file__).resolve().parent.parent / 'app' / 'static' / 'js' / 'main.js'
    assert js_path.exists(), "main.js must exist"
    content = js_path.read_text(encoding='utf-8')
    assert 'initAlertDismissal' in content
    assert 'initFileInputs' in content
    assert 'initDropzones' in content
    assert 'initCopyButtons' in content
