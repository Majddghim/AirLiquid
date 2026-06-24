from flask import Blueprint, render_template, redirect, session, jsonify, request, url_for
from services.employe import EmployeService
from services.admin import AdminService


class GuestViews:
    def __init__(self):
        self.guest_bp = Blueprint('guest', __name__, template_folder='templates')
        self.EmployeService = EmployeService()
        self.Admin_Service = AdminService()
        self.guest_routes()

    def guest_routes(self):

        @self.guest_bp.route('/login', methods=['GET'])
        def home_page():
            return render_template('guest/login.html')

        @self.guest_bp.route('/login', methods=['POST'])
        def login():
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return jsonify({'status': 'failed', 'message': 'Email et mot de passe requis'})

            emp, error = self.EmployeService.authenticate_employee(email, password)
            if error:
                return jsonify({'status': 'failed', 'message': error})

            session['email'] = emp['email']
            session['user_id'] = emp['id']
            return jsonify({'status': 'success', 'redirect': url_for('guest.home')})

        @self.guest_bp.route('/home', methods=['GET'])
        def home():
            if 'email' not in session:
                return redirect(url_for('guest.home_page'))

            from services.voiture import VoitureService
            employee = self.Admin_Service.get_employe_by_email(session['email'])
            if not employee:
                return "Employé introuvable", 404

            voitures = VoitureService().get_carte_grise_by_owner_name(employee['id'])
            return render_template('guest/home.html', employee=employee, voitures=voitures)

        @self.guest_bp.route('/logout', methods=['GET'])
        def logout():
            session.clear()
            return redirect(url_for('guest.home_page'))
