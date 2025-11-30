from flask import Blueprint, render_template, redirect, session, jsonify, request, url_for

from services.admin import AdminService
from services.voiture import VoitureService     # ← Make sure this exists
from tools.database_tools import DatabaseTools


class GuestViews:
    def __init__(self):
        self.guest_bp = Blueprint('guest', __name__, template_folder='templates')
        self.db_tools = DatabaseTools()
        self.Admin_Service = AdminService()
        self.Voiture_Service = VoitureService()   # ← Needed for car search

        self.guest_routes()

    def guest_routes(self):

        # ------------------ LOGIN PAGE ------------------
        @self.guest_bp.route('/login', methods=['GET'])
        def home_page():
            return render_template('guest/login.html')

        # ------------------ LOGIN SUBMIT ------------------
        @self.guest_bp.route('/login', methods=['POST'])
        def login():
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            # Validate input
            if not email:
                return jsonify({'status': 'failed', 'message': 'Email is required'})
            if not password:
                return jsonify({'status': 'failed', 'message': 'Password is required'})

            # Get employee by email
            user = self.Admin_Service.get_employe_by_email(email)
            if user is None:
                return jsonify({'status': 'failed', 'message': 'Utilisateur non trouvé'})

            # Check password
            if user['password'] != password:
                return jsonify({'status': 'failed', 'message': 'Mot de passe incorrect'})

            # Store user email in session
            session['email'] = user['email']
            session['user_id'] = user['id']

            print("User logged in:", session['email'])

            return jsonify({'status': 'success', 'redirect': url_for('guest.home')})

        # ------------------ HOME PAGE (CARS OF USER) ------------------
        @self.guest_bp.route('/home', methods=['GET'])
        def home():
            email = session.get('email')

            if not email:
                return redirect(url_for('guest.home_page'))  # Not logged in → go to login

            # Get employee info
            employee = self.Admin_Service.get_employe_by_email(email)
            print(employee)
            if not employee:
                return "Employee not found", 404

            owner_name = f"{employee['username']}"

            # Get cars owned by this person
            voitures = self.Voiture_Service.get_carte_grise_by_owner_name(employee['id'])

            return render_template('guest/home.html',
                                   employee=employee,
                                   voitures=voitures)

        # ------------------ LOGOUT ------------------
        @self.guest_bp.route('/logout', methods=['GET'])
        def logout():
            session.clear()
            return redirect(url_for('guest.home_page'))
