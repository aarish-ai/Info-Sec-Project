import os
import shutil
import tempfile
import pytest
from app import create_app
from app.database.db import get_db, init_db

@pytest.fixture
def app():
    """Create and configure a clean Flask application for testing."""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    key_storage_dir = tempfile.mkdtemp(prefix='mediaguard_keys_')
    media_dir = tempfile.mkdtemp(prefix='mediaguard_media_')

    test_app = create_app({
        'TESTING': True,
        'DATABASE_PATH': db_path,
        'KEY_STORAGE_DIR': key_storage_dir,
        'ENCRYPTED_MEDIA_DIR': media_dir,
        'SECRET_KEY': 'test-secret-key',
    })

    with test_app.app_context():
        init_db()
        yield test_app

    # Cleanup after test
    os.close(db_fd)
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except OSError:
            pass
    if os.path.exists(key_storage_dir):
        shutil.rmtree(key_storage_dir, ignore_errors=True)
    if os.path.exists(media_dir):
        shutil.rmtree(media_dir, ignore_errors=True)

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def db(app):
    """Get database connection for tests."""
    with app.app_context():
        yield get_db()
