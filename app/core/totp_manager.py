import io
import qrcode
from app.core.custom_crypto.totp import CustomTOTP, generate_base32_secret

def generate_totp_secret() -> str:
    """
    Generates a cryptographically secure random 32-character Base32 secret string
    for RFC 6238 Time-Based One-Time Password (TOTP) generation.
    """
    return generate_base32_secret()

def get_totp_uri(username: str, secret: str, issuer_name: str = "MediaGuard") -> str:
    """
    Constructs the standard otpauth:// provisioning URI for 2FA authenticator apps
    (Google Authenticator, Aegis, 1Password, etc.).
    """
    totp = CustomTOTP(secret)
    return totp.provisioning_uri(name=username, issuer_name=issuer_name)

def generate_totp_qr_png(uri: str) -> bytes:
    """
    Generates a high-contrast QR code image for a provisioning URI
    and returns the raw PNG byte content.
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()

def verify_totp_code(secret: str, code: str, valid_window: int = 1) -> bool:
    """
    Verifies a 6-digit TOTP code against the shared Base32 secret.
    Allows clock drift via valid_window (default 1 step = +/- 30 seconds).
    Returns True if valid, False otherwise.
    """
    if not secret or not code:
        return False
    try:
        clean_code = str(code).strip()
        totp = CustomTOTP(secret)
        return bool(totp.verify(clean_code, valid_window=valid_window))
    except Exception:
        return False
