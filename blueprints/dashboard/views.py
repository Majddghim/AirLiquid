from flask import blueprints, render_template, redirect, session, jsonify, request, url_for
from entities.admin import Admin
from blueprints.auth.views import AuthViews
class DashboardViews :
    def __init__(self):
        self.admin_bp= blueprints .Blueprint('dashboard', __name__, template_folder='templates')
        self.admin_routes()

    def admin_routes(self):
        @self.admin_bp.route('/dashboard')
        def admin_dashboard():
            if 'user' not in session or not session['dashboard']:
                return redirect(url_for("auth.login_template"))
            return render_template('dashboard.html')