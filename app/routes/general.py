from flask import Blueprint, render_template

general_bp = Blueprint('general', __name__)

@general_bp.route('/')
def index():
    """Renders the MediaGuard public landing page."""
    return render_template('index.html')
