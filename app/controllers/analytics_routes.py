from flask import render_template, jsonify, request
from flask_login import login_required
from app import cache
from app.services.analytics_service import get_dashboard_data
from . import main_bp


@main_bp.route('/dashboard')
@login_required
@cache.cached()
def dashboard():
    """Renderiza a página do dashboard analítico"""
    # O período pode ser passado via query string, default é 6 meses
    months = request.args.get('months', 6, type=int)
    return render_template('analytics/dashboard.html', periodo_meses=months)

@main_bp.route('/api/analytics/data')
@login_required
def get_data():
    """Endpoint API para obter os dados do dashboard"""
    # O período pode ser passado via query string, default é 6 meses
    months = request.args.get('months', 6, type=int)
    return jsonify(get_dashboard_data(months))
