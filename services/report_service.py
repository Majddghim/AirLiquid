from tools.database_tools import DatabaseTools
import re


class ReportService:
    def __init__(self):
        self.db = DatabaseTools()

    def execute_report_query(self, sql):
        """Execute a SELECT query and return results as list of dicts"""
        # security: only allow SELECT
        sql_clean = sql.strip().upper()
        if not sql_clean.startswith('SELECT'):
            raise ValueError('Seules les requêtes SELECT sont autorisées')

        # block dangerous keywords
        forbidden = ['DELETE', 'UPDATE', 'INSERT', 'DROP', 'ALTER',
                     'CREATE', 'TRUNCATE', 'EXEC', 'EXECUTE']
        for word in forbidden:
            if re.search(r'\b' + word + r'\b', sql_clean):
                raise ValueError(f'Requête non autorisée: contient {word}')

        con, cursor = self.db.find_connection()
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            if not rows:
                return [], []
            headers = list(rows[0].keys())
            data    = [list(r.values()) for r in rows]
            return headers, data
        finally:
            con.close()