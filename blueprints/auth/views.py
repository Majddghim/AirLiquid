from flask import Blueprint, render_template, session, redirect, url_for, jsonify, request
from werkzeug.security import check_password_hash
from services.admin import AdminService
from services.audit_service import AuditService


class AuthViews:
    def __init__(self):
        self.Admin_Service = AdminService()
        self.audit = AuditService()
        self.auth_bp = Blueprint('auth', __name__, template_folder='templates')
        self.auth_routes()

    def auth_routes(self):
        @self.auth_bp.route('/login', methods=['GET'])
        def login_template():
            if 'user_id' in session:
                return redirect(url_for('dashboard.admin_dashboard'))
            return render_template('login.html')

        @self.auth_bp.route('/login', methods=['POST'])
        def login():
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')

            if not email or not password:
                return jsonify({'status': 'failed', 'message': 'Email and password are required'})

            user = self.Admin_Service.get_admin_by_email(email)
            if user is None:
                return jsonify({'status': 'failed', 'message': 'Utilisateur non trouvé'})

            if not check_password_hash(user.password_hash, password):
                return jsonify({'status': 'failed', 'message': 'Mot de passe incorrect'})

            session['user_id'] = user.id
            self.audit.log('login', 'admin', user.id, user_id=user.id)
            return jsonify({'status': 'success', 'redirect': url_for('dashboard.admin_dashboard')})

        @self.auth_bp.route('/logout', methods=['GET'])
        def logout():
            user_id = session.get('user_id')
            session.pop('user_id', None)
            if user_id:
                self.audit.log('logout', 'admin', user_id, user_id=user_id)
            return redirect(url_for('auth.login_template'))
