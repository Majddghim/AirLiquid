import self
from flask import blueprints, render_template, redirect, session, jsonify, request, url_for,render_template
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

        @self.admin_bp.route('/employe')
        def employe_page():
            return render_template('employe.html')

        @self.admin_bp.route('/profile')
        def profile_page():
            return render_template('profile.html')

        @self.admin_bp.route('/ajout-employe')
        def ajout_employe_page():
            return render_template('ajout-employe.html')

        @self.admin_bp.route('/ajout-voiture')
        def ajout_admin_page():
            return render_template('ajout-voiture.html')

        @self.admin_bp.route('/ajout-voiture/<int:eid>')
        def ajout_voiture_avec_id(eid):
            return render_template('ajout-voiture.html', employe_id=eid)