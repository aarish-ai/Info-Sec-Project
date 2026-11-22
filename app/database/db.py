import sqlite3
from pathlib import Path
from flask import g, current_app, has_app_context
from config import Config

SCHEMA_PATH = Path(__file__).resolve().parent / 'schema.sql'

def get_db(db_path=None) -> sqlite3.Connection:
    """
    Get a database connection with foreign keys enabled and sqlite3.Row factory.
    Uses Flask's application context `g` if available, otherwise returns a standalone connection.
    """
    if has_app_context():
        if 'db' not in g:
            target_path = db_path or current_app.config.get('DATABASE_PATH', Config.DATABASE_PATH)
            # Ensure parent directory exists
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)
            g.db = sqlite3.connect(
                target_path,
                detect_types=sqlite3.PARSE_DECLTYPES
            )
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON;")
        return g.db

    # Standalone connection when outside Flask context
    target_path = db_path or Config.DATABASE_PATH
    Path(target_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(
        target_path,
        detect_types=sqlite3.PARSE_DECLTYPES
    )
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def close_db(e=None):
    """Close the current database connection if one exists in Flask g context."""
    if has_app_context():
        db = g.pop('db', None)
        if db is not None:
            db.close()

def init_db(app=None, db_path=None):
    """Initialize database tables using schema.sql."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    if has_app_context():
        db = get_db(db_path)
        db.executescript(schema_sql)
        db.commit()
    else:
        conn = get_db(db_path)
        conn.executescript(schema_sql)
        conn.commit()
        conn.close()

def init_app(app):
    """Register database teardown function with Flask application."""
    app.teardown_appcontext(close_db)
