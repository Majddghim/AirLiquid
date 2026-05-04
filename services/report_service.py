from tools.database_tools import DatabaseTools
import re


class ReportService:
    def __init__(self):
        self.db = DatabaseTools()

    def execute_report_query(self, sql):
        """Execute a SELECT query and return headers + rows"""

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

            all_headers = list(rows[0].keys())

            # filter out internal ID columns
            id_columns = {
                'id', 'car_id', 'employee_id', 'part_id', 'garage_id',
                'current_cg_id', 'assigned_by_admin_id', 'verified_by_admin_id',
                'reference_id', 'brand_id', 'departement_id', 'cg_id'
            }
            keep = [h for h in all_headers if h.lower() not in id_columns]

            headers = keep
            data    = [[r[h] for h in keep] for r in rows]
            return headers, data
        finally:
            con.close()