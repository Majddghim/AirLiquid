from flask import blueprints, render_template, redirect, session, jsonify, request, url_for, render_template

from services.admin import AdminService
from tools.database_tools import DatabaseTools


class GuestViews:
    def __init__(self):
        self.guest_bp = blueprints.Blueprint('guest', __name__, template_folder='templates')
        self.db_tools = DatabaseTools()
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
            if not email and password:
                print("Email missing")
                return jsonify({'status': 'failed', 'message': 'Email is required'})

            if not password and email:
                print("Password missing")
                return jsonify({'status': 'failed', 'message': 'Password is required'})

            if not email or not password:
                print("missing email or password")
                return jsonify({'status': 'failed', 'message': 'Email and password are required'})

            # if '@' not in email:
            # print("Invalid email format")
            # return jsonify({'status': 'failed', 'message': 'Invalid email format'})

            user = self.Admin_Service.get_employe_by_email(email)
            if user is None:
                return jsonify({'status': 'failed', 'message': 'Utilisateur non trouvé'})
            if user is None:
                print(user, 'failed')
                return jsonify({'status': 'error', 'message': 'Something went wrong'})
            print("user found:", user)
            if not user or user['password'] != password:
                return jsonify({'status': 'failed', 'message': 'mot de passe incorrect'})
            session['user_id'] = user['id']
            print(session['user_id'], 'logged in successfully')
            return jsonify({'status': 'success', 'redirect': url_for('dashboard.admin_dashboard')})

        @self.guest_bp.route('/home', methods=['GET'])
        def home():
            return render_template('guest/home.html')

        @self.guest_bp.route('/logout', methods=['GET'])
        def logout():
            session.pop('user_id', None)
            return redirect(url_for('guest.home_page'))



