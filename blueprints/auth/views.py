from flask import Blueprint, render_template, session, redirect, url_for, jsonify , request

from services.admin import AdminService

class AuthViews:
    def __init__(self):
        self.Admin_Service = AdminService()
        self.auth_bp = Blueprint('auth', __name__, template_folder='templates')
        self.auth_routes()

    def auth_routes(self):
        @self.auth_bp.route('/login', methods=['GET'])
        def login_template():
            if 'user_id' in session:
                return redirect(url_for('dashboard.dashboard_home'))
            return render_template('login.html')

        @self.auth_bp.route('/login', methods=['POST'])
        def login():

            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
            if not email and password :
                print("Email missing")
                return jsonify({'status': 'failed', 'message': 'Email is required'})

            if not password and email:
                print("Password missing")
                return jsonify({'status': 'failed', 'message': 'Password is required'})

            if not email or not password:
                print("missing email or password")
                return jsonify({'status': 'failed', 'message': 'Email and password are required'})

            #if '@' not in email:
                #print("Invalid email format")
                #return jsonify({'status': 'failed', 'message': 'Invalid email format'})

            user = self.Admin_Service.get_admin_by_email(email)
            if user is None:
                return jsonify({'status': 'failed', 'message': 'Utilisateur non trouvé'})
            if user is None:
                print(user, 'failed')
                return jsonify({'status': 'error', 'message': 'Something went wrong'})
            print("user found:", user)
            if not user or user.password != password:
                return jsonify({'status': 'failed', 'message': 'mot de passe incorrect'})
            session['user_id'] = user.id
            print(session['user_id'], 'logged in successfully')
            return jsonify({'status': 'success', 'redirect': url_for('dashboard.admin_dashboard')})

        @self.auth_bp.route('/logout', methods=['GET'])
        def logout():
            session.pop('user', None)
            return redirect(url_for('auth.login_template'))