from tools.database_tools import DatabaseTools
import datetime


class MessageService:
    def __init__(self):
        self.db = DatabaseTools()

    def send_message(self, sender_type, sender_id, receiver_type, receiver_id, content):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                INSERT INTO messages (sender_type, sender_id, receiver_type, receiver_id, content)
                VALUES (%s, %s, %s, %s, %s)
            """, (sender_type, sender_id, receiver_type, receiver_id, content))
            con.commit()
            return cursor.lastrowid
        finally:
            con.close()

    def get_conversation(self, admin_id, employee_id):
        """Get all messages between admin and employee"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT m.*, 
                       CASE WHEN m.sender_type = 'admin' THEN 'RH'
                            ELSE CONCAT(e.prenom, ' ', e.nom)
                       END AS sender_name
                FROM messages m
                LEFT JOIN employees e ON m.sender_type = 'employee' AND m.sender_id = e.id
                WHERE (m.sender_type = 'admin' AND m.sender_id = %s 
                       AND m.receiver_type = 'employee' AND m.receiver_id = %s)
                OR    (m.sender_type = 'employee' AND m.sender_id = %s 
                       AND m.receiver_type = 'admin' AND m.receiver_id = %s)
                ORDER BY m.created_at ASC
            """, (admin_id, employee_id, employee_id, admin_id))
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()

    def mark_as_read(self, receiver_type, receiver_id, sender_type, sender_id):
        """Mark all messages from sender as read"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                UPDATE messages SET is_read = 1
                WHERE receiver_type = %s AND receiver_id = %s
                AND sender_type = %s AND sender_id = %s
                AND is_read = 0
            """, (receiver_type, receiver_id, sender_type, sender_id))
            con.commit()
        finally:
            con.close()

    def get_unread_count(self, receiver_type, receiver_id):
        """Get total unread messages count"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM messages
                WHERE receiver_type = %s AND receiver_id = %s AND is_read = 0
            """, (receiver_type, receiver_id))
            return cursor.fetchone()['cnt']
        finally:
            con.close()

    def get_unread_per_employee(self, admin_id):
        """Get unread count per employee for admin"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT sender_id AS employee_id, COUNT(*) AS cnt
                FROM messages
                WHERE receiver_type = 'admin' AND receiver_id = %s
                AND sender_type = 'employee' AND is_read = 0
                GROUP BY sender_id
            """, (admin_id,))
            rows = cursor.fetchall()
            return {r['employee_id']: r['cnt'] for r in rows}
        finally:
            con.close()

    def get_employee_conversations(self, employee_id):
        """Get all messages for an employee (with admin)"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT m.*,
                       CASE WHEN m.sender_type = 'admin' THEN 'RH'
                            ELSE CONCAT(e.prenom, ' ', e.nom)
                       END AS sender_name
                FROM messages m
                LEFT JOIN employees e ON m.sender_type = 'employee' AND m.sender_id = e.id
                WHERE (m.sender_type = 'employee' AND m.sender_id = %s)
                OR    (m.receiver_type = 'employee' AND m.receiver_id = %s)
                ORDER BY m.created_at ASC
            """, (employee_id, employee_id))
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()