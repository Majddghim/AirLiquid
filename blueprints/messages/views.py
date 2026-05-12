from flask import Blueprint, request, jsonify, session
from services.message_service import MessageService


class MessageViews:
    def __init__(self):
        self.service    = MessageService()
        self.message_bp = Blueprint('messages', __name__)
        self.message_routes()

    def message_routes(self):

        @self.message_bp.route('/conversation/<int:employee_id>', methods=['GET'])
        def get_conversation(employee_id):
            try:
                messages = self.service.get_conversation(
                    admin_id=1,
                    employee_id=employee_id
                )
                # mark employee messages as read
                self.service.mark_as_read(
                    receiver_type='admin', receiver_id=1,
                    sender_type='employee', sender_id=employee_id
                )
                # serialize dates
                for m in messages:
                    if m.get('created_at'):
                        m['created_at'] = str(m['created_at'])
                return jsonify({'status': 'success', 'data': messages})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.message_bp.route('/send', methods=['POST'])
        def send_message():
            try:
                data     = request.get_json()
                msg_type = data.get('sender_type')
                if msg_type == 'admin':
                    self.service.send_message(
                        sender_type='admin',
                        sender_id=1,
                        receiver_type='employee',
                        receiver_id=data.get('employee_id'),
                        content=data.get('content')
                    )
                else:
                    if 'employe_id' not in session:
                        return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401
                    self.service.send_message(
                        sender_type='employee',
                        sender_id=session['employe_id'],
                        receiver_type='admin',
                        receiver_id=1,
                        content=data.get('content')
                    )
                return jsonify({'status': 'success', 'message': 'Message envoyé'})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.message_bp.route('/unread', methods=['GET'])
        def unread_count():
            try:
                count = self.service.get_unread_count(
                    receiver_type='admin', receiver_id=1
                )
                return jsonify({'status': 'success', 'count': count})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.message_bp.route('/unread-per-employee', methods=['GET'])
        def unread_per_employee():
            try:
                data = self.service.get_unread_per_employee(admin_id=1)
                return jsonify({'status': 'success', 'data': data})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500

        @self.message_bp.route('/employee-messages', methods=['GET'])
        def employee_messages():
            try:
                if 'employe_id' not in session:
                    return jsonify({'status': 'failed', 'message': 'Non connecté'}), 401
                messages = self.service.get_employee_conversations(
                    employee_id=session['employe_id']
                )
                # mark admin messages as read
                self.service.mark_as_read(
                    receiver_type='employee',
                    receiver_id=session['employe_id'],
                    sender_type='admin',
                    sender_id=1
                )
                for m in messages:
                    if m.get('created_at'):
                        m['created_at'] = str(m['created_at'])
                return jsonify({'status': 'success', 'data': messages})
            except Exception as e:
                return jsonify({'status': 'failed', 'message': str(e)}), 500