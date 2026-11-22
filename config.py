import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mediaguard-dev-secret-key-change-in-prod')
    DATABASE_PATH = BASE_DIR / 'app' / 'database' / 'mediaguard.db'
    ENCRYPTED_MEDIA_DIR = BASE_DIR / 'storage' / 'encrypted_media'
    KEY_STORAGE_DIR = BASE_DIR / 'storage' / 'key_storage'
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB Cap
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'mp4', 'mov'}
    ALLOWED_MIME_TYPES = {
        'image/jpeg', 'image/png', 'video/mp4', 'video/quicktime'
    }
    # Dynamic demonstration switch for OWASP Top 10 Before/After viva demo
    SECURE_MODE = True
