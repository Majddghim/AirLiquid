import json

from tools.database_tools import DatabaseTools


class AuditService:
    def __init__(self):
        self.db = DatabaseTools()

    def log(self, action, entity_type, entity_id, user_id=None, details=None, user_type='admin', ip_address=None):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                INSERT INTO audit_log (user_id, user_type, action, table_name, record_id, details, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, user_type, action, entity_type, entity_id, json.dumps(details), ip_address))
            con.commit()
            return cursor.lastrowid
        finally:
            con.close()

    def get_logs(self, entity_type=None, entity_id=None, limit=100):
        con, cursor = self.db.find_connection()
        try:
            query = "SELECT * FROM audit_log"
            params = []
            conditions = []
            if entity_type:
                conditions.append("table_name = %s")
                params.append(entity_type)
            if entity_id:
                conditions.append("record_id = %s")
                params.append(entity_id)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            cursor.execute(query, params)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()
