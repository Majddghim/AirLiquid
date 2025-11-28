
from flask import blueprints, render_template, redirect, session, jsonify, request, url_for,render_template
from entities.admin import Admin
from blueprints.auth.views import AuthViews
from blueprints.car.views import CarViews
from services.employe import EmployeService
from services.voiture import VoitureService


class DashboardViews :
    def __init__(self):
        self.VoitureService = VoitureService()
        self.EmployeService = EmployeService()
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

        @self.admin_bp.route('/voiture')
        def voiture_page():
            return render_template('voiture.html')

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

        @self.admin_bp.route('/liste-employes', methods=['GET'])
        def get_employes():
            data = self.EmployeService.get_all_employes()
            if data is None or len(data) == 0:
                return jsonify({'status': 'failed', 'message': 'No employes found'})
            print(data)
            return render_template('employe2.html', data=data)
        
        @self.admin_bp.route('/cars', methods=['GET'])
        def cars_page():
            voitures = self.VoitureService.get_all_carte_grises()
            return render_template('car.html', voitures=voitures)