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
from app.routes.auth import login_required
from experiments.attack_simulations import (
    ATTACK_CATALOG,
    run_named_attack_simulation
)

experiments_bp = Blueprint('experiments', __name__, url_prefix='/experiments')

def _wants_json():
    """Determine whether the request expects a JSON API response."""
    return (
        request.is_json
        or request.path.startswith('/api/')
        or 'application/json' in request.headers.get('Accept', '')
    )

@experiments_bp.route('', methods=['GET'])
@experiments_bp.route('/', methods=['GET'])
@login_required
def simulations_dashboard():
    """
    Security Attack Simulation Dashboard.
    Interactive academic laboratory allowing evaluators and students to execute
    6 controlled attacks and observe real-time cryptographic defense countermeasures.
    """
    attacks = list(ATTACK_CATALOG.values())
    if _wants_json():
        return jsonify({
            'success': True,
            'count': len(attacks),
            'attacks': attacks
        }), 200

    return render_template('experiments/simulations.html', attacks=attacks)

@experiments_bp.route('/run/<attack_name>', methods=['POST'])
@login_required
def run_simulation(attack_name):
    """
    Executes a specific security attack simulation and returns diagnostic results.
    """
    if attack_name not in ATTACK_CATALOG:
        if _wants_json():
            return jsonify({'error': f"Unknown attack simulation '{attack_name}'"}), 404
        flash(f"Unknown attack simulation '{attack_name}'", 'danger')
        return redirect(url_for('experiments.simulations_dashboard'))

    result = run_named_attack_simulation(attack_name)

    if _wants_json():
        return jsonify(result), 200

    return render_template(
        'experiments/simulations.html',
        attacks=list(ATTACK_CATALOG.values()),
        active_result=result
    )
