from flask import blueprints, render_template, redirect, session, jsonify, request, url_for
from services.employe import EmployeService
from services.voiture import VoitureService
from services.dashboard_service import DashboardService


class DashboardViews:
    def __init__(self):
        self.VoitureService   = VoitureService()
        self.EmployeService   = EmployeService()
        self.DashboardService = DashboardService()
        self.admin_bp = blueprints.Blueprint('dashboard', __name__, template_folder='templates')
        self.admin_routes()

    def admin_routes(self):

        # ------------------------------------------------------------------ #
        # EXISTING PAGE ROUTES — untouched                                    #
        # ------------------------------------------------------------------ #

        @self.admin_bp.route('/')
        def admin_dashboard():
            if 'user_id' not in session:
                return redirect(url_for("auth.login_template"))
            return render_template('dashboard.html')

        @self.admin_bp.route('/employe')
        def employe_page():
            if 'user_id' not in session:
                return redirect(url_for("auth.login_template"))
            return render_template('employe.html')

        @self.admin_bp.route('/voiture')
        def voiture_page():
            if 'user_id' not in session:
                return redirect(url_for("auth.login_template"))
            return render_template('voiture.html')

        @self.admin_bp.route('/profile')
        def profile_page():
            if 'user_id' not in session:
                return redirect(url_for("auth.login_template"))
            return render_template('profile.html')

        @self.admin_bp.route('/ajout-employe')
        def ajout_employe_page():
            if 'user_id' not in session:
                return redirect(url_for("auth.login_template"))
            return render_template('ajout-employe.html')

        @self.admin_bp.route('/ajout-voiture')
        def ajout_voiture_page():
            if 'user_id' not in session:
                return redirect(url_for("auth.login_template"))
            return render_template('ajout-voiture.html')

        @self.admin_bp.route('/ajout-voiture/<int:eid>')
        def ajout_voiture_avec_id(eid):
            if 'user_id' not in session:
                return redirect(url_for("auth.login_template"))
            return render_template('ajout-voiture.html', employe_id=eid)

        @self.admin_bp.route('/liste-employes', methods=['GET'])
        def get_employes_page():
            if 'user_id' not in session:
                return redirect(url_for("auth.login_template"))
            data = self.EmployeService.get_all_employes()
            return render_template('employe2.html', data=data)

        @self.admin_bp.route('/cars', methods=['GET'])
        def cars_page():
            if 'user_id' not in session:
                return redirect(url_for("auth.login_template"))
            voitures = self.VoitureService.get_all_voitures()
            return render_template('car.html', voitures=voitures)

        # ------------------------------------------------------------------ #
        # DASHBOARD DATA ROUTES                                               #
        # ------------------------------------------------------------------ #

        @self.admin_bp.route('/api/fleet-kpis', methods=['GET'])
        def fleet_kpis():
            try:
                data = self.DashboardService.get_fleet_kpis()
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.admin_bp.route('/api/expense-kpis', methods=['GET'])
        def expense_kpis():
            try:
                date_from = request.args.get('from')
                date_to   = request.args.get('to')
                data = self.DashboardService.get_expense_kpis(date_from, date_to)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.admin_bp.route('/api/monthly-expenses', methods=['GET'])
        def monthly_expenses():
            try:
                date_from = request.args.get('from')
                date_to   = request.args.get('to')
                data = self.DashboardService.get_monthly_expenses(date_from, date_to)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                import traceback
                print(traceback.format_exc())  # add this line
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.admin_bp.route('/api/top-cars', methods=['GET'])
        def top_cars():
            try:
                date_from = request.args.get('from')
                date_to   = request.args.get('to')
                data = self.DashboardService.get_top_expensive_cars(date_from, date_to)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.admin_bp.route('/api/alerts', methods=['GET'])
        def alerts():
            try:
                days = request.args.get('days', 30, type=int)
                data = self.DashboardService.get_alerts(days)
                return jsonify({'status': 'success', 'data': data, 'count': len(data)})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500