import os
from flask import Blueprint, request, jsonify, redirect, session
from tools.gmail_tools import GmailTools


class GmailViews:
    def __init__(self):
        self.gmail_bp = Blueprint('gmail', __name__)
        self.gmail_routes()

    def gmail_routes(self):

        @self.gmail_bp.route('/connect', methods=['GET'])
        def connect():
            try:
                os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
                tools           = GmailTools()
                auth_url, state = tools.get_auth_url()
                session['gmail_state'] = state
                return redirect(auth_url)
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.gmail_bp.route('/callback', methods=['GET'])
        def callback():
            try:
                os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
                code  = request.args.get('code')
                tools = GmailTools()
                tools.exchange_code(code)
                return redirect('/dashboard/?gmail=connected')
            except Exception as e:
                return f'Erreur: {str(e)}', 500

        @self.gmail_bp.route('/status', methods=['GET'])
        def status():
            try:
                tools = GmailTools()
                return jsonify({
                    'status':    'success',
                    'connected': tools.is_connected()
                })
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.gmail_bp.route('/emails', methods=['GET'])
        def get_emails():
            try:
                tools = GmailTools()
                if not tools.is_connected():
                    return jsonify({'status': 'failed', 'message': 'Gmail non connecté'})
                emails = tools.fetch_fleet_emails(max_results=30)
                return jsonify({'status': 'success', 'data': emails, 'count': len(emails)})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.gmail_bp.route('/disconnect', methods=['POST'])
        def disconnect():
            try:
                if os.path.exists('gmail_token.json'):
                    os.remove('gmail_token.json')
                return jsonify({'status': 'success', 'message': 'Gmail déconnecté'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500