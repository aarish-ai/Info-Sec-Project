from flask import (
    Blueprint,
    request,
    jsonify,
    render_template,
    flash,
    redirect,
    url_for,
    current_app
)
from app.database.db import get_db
from app.routes.auth import login_required, require_role
from app.core.audit_chain import verify_audit_chain

audit_bp = Blueprint('audit', __name__, url_prefix='/audit')

def _wants_json():
    """Determine whether the request expects a JSON API response."""
    return (
        request.is_json
        or request.path.startswith('/api/')
        or 'application/json' in request.headers.get('Accept', '')
    )

@audit_bp.route('', methods=['GET'])
@audit_bp.route('/', methods=['GET'])
@login_required
@require_role('Auditor', 'Admin')
def audit_dashboard():
    """
    Immutable Cryptographic Audit Trail Dashboard.
    Restricted strictly to Auditor and Admin roles.
    Displays tamper-evident audit logs with pagination and search.
    """
    db = get_db()
    cursor = db.cursor()

    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = max(0, (page - 1) * per_page)

    base_query = """
        SELECT 
            a.log_id, a.timestamp, a.user_id, a.action, a.details,
            a.ip_address, a.prev_hash, a.current_hash,
            u.username, u.role as user_role
        FROM audit_log a
        LEFT JOIN users u ON a.user_id = u.user_id
    """

    if query:
        filter_sql = """
            WHERE a.action LIKE ? 
               OR a.details LIKE ? 
               OR u.username LIKE ? 
               OR a.ip_address LIKE ?
               OR a.current_hash LIKE ?
        """
        like_pattern = f"%{query}%"
        params = (like_pattern, like_pattern, like_pattern, like_pattern, like_pattern)
        
        count_cursor = db.cursor()
        count_cursor.execute(f"SELECT COUNT(*) as total FROM audit_log a LEFT JOIN users u ON a.user_id = u.user_id {filter_sql}", params)
        total = count_cursor.fetchone()['total']

        cursor.execute(
            f"{base_query} {filter_sql} ORDER BY a.log_id DESC LIMIT ? OFFSET ?",
            (*params, per_page, offset)
        )
    else:
        count_cursor = db.cursor()
        count_cursor.execute("SELECT COUNT(*) as total FROM audit_log")
        total = count_cursor.fetchone()['total']

        cursor.execute(
            f"{base_query} ORDER BY a.log_id DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        )

    rows = cursor.fetchall()
    logs = [dict(row) for row in rows]

    if _wants_json():
        return jsonify({
            'success': True,
            'count': len(logs),
            'total': total,
            'page': page,
            'per_page': per_page,
            'logs': logs
        }), 200

    return render_template(
        'audit/audit_log.html',
        logs=logs,
        total=total,
        query=query,
        page=page
    )

@audit_bp.route('/verify-chain', methods=['POST'])
@login_required
@require_role('Auditor', 'Admin')
def verify_chain():
    """
    Executes a complete verification of the cryptographic audit log hash chain.
    Recalculates SHA-256 for every block from genesis to head and verifies prev_hash linkage.
    """
    db = get_db()
    is_valid, corrupted_id, message = verify_audit_chain(db)

    if _wants_json():
        return jsonify({
            'success': True,
            'valid': is_valid,
            'corrupted_log_id': corrupted_id,
            'message': message
        }), 200

    if is_valid:
        flash(message, 'success')
    else:
        flash(message, 'danger')

    return redirect(url_for('audit.audit_dashboard'))
