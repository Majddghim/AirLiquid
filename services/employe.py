from tools.database_tools import DatabaseTools
from entities.employe import Employe


class EmployeService:
    def __init__(self):
        self.db_tools = DatabaseTools()

    def get_employe_by_something(self, condition, order='', limit='', dict_form=True):
        con, cursor = self.db_tools.find_connection()
        query = f"""SELECT id, nom, prenom, departement, poste, email, telephone, status, created_at, updated_at FROM employees WHERE {condition} {order} {limit} """
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
        con.close()
        le = []
        if result:
            for employe_data in result:
                e = Employe(
                    id=employe_data['id'],
                    nom=employe_data['nom'],
                    prenom=employe_data['prenom'],
                    departement=employe_data['departement'],
                    poste=employe_data['poste'],
                    email=employe_data['email'],
                    telephone=employe_data['telephone'],
                    status=employe_data['status'],
                    created_at=employe_data['created_at'],
                    updated_at=employe_data['updated_at']
                )
                if dict_form:
                    le.append(e.__dict__())
                else:
                    le.append(e)
            return le
        return []

    def get_employe_by_email(self, email):
        return self.get_employe_by_something(f" email = '{email}' ")

    def get_employe_by_id(self, id):
        con, cursor = self.db_tools.find_connection()
        query = "SELECT id, nom, prenom, departement, poste, email, telephone, status, created_at, updated_at FROM employees WHERE id = %s"
        cursor.execute(query, (id,))
        result = cursor.fetchall()
        con.close()
        if result:
            emp_data = result[0]
            return Employe(
                id=emp_data['id'],
                nom=emp_data['nom'],
                prenom=emp_data['prenom'],
                departement=emp_data['departement'],
                poste=emp_data['poste'],
                email=emp_data['email'],
                telephone=emp_data['telephone'],
                status=emp_data['status'],
                created_at=emp_data['created_at'],
                updated_at=emp_data['updated_at']
            )
        return None

    def get_all_employes(self):
        return self.get_employe_by_something(" 1=1 ")

    def add_employe(self, nom, prenom, departement, poste, email, telephone, created_at):
        con, cursor = self.db_tools.find_connection()
        query = """
        INSERT INTO employees (nom, prenom, departement, poste, email, telephone, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (nom, prenom, departement, poste, email, telephone, created_at))
        con.commit()
        last_id = cursor.lastrowid
        con.close()
        return last_id

    def get_employe_by_name(self, search_by_name, number=None, begin=None, dict_form=True):
        limit = ''
        if number is not None and begin is not None:
            limit = f"LIMIT {str(begin)}, {str(number)}"
        count_res = self.get_count_employe_something(
            f"( nom LIKE '%{search_by_name}%' OR prenom LIKE '%{search_by_name}%' )")

        employes = self.get_employe_by_something(
            f"( nom LIKE '%{search_by_name}%' OR prenom LIKE '%{search_by_name}%' )",
            limit=limit,
            dict_form=dict_form)

        return employes, count_res[1]['num'] if count_res[0] == 'success' else 0

    def get_count_employe_something(self, condition):
        try:
            con, cursor = self.db_tools.find_connection()
            cursor.execute(f"""
                SELECT COUNT(id) AS num
                FROM employees
                WHERE {condition}
            """)
            data = cursor.fetchone()
            cursor.close()
            con.close()
            if not data:
                return 'failed', 'No employe found'
            return 'success', data
        except Exception as e:
            return 'failed', str(e)

    # ------------------------------------------------------------------ #
    # DÉPARTEMENTS & POSTES                                                #
    # ------------------------------------------------------------------ #

    def get_departements(self):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("SELECT id, name FROM departements ORDER BY name ASC")
            return cursor.fetchall()
        finally:
            con.close()

    def get_postes_by_departement(self, departement_id):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute(
                "SELECT id, name FROM postes WHERE departement_id = %s ORDER BY name ASC",
                (departement_id,)
            )
            return cursor.fetchall()
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # UPDATE, DELETE, AFFECTATION                                          #
    # ------------------------------------------------------------------ #

    def update_employe(self, employe_id, nom, prenom, email, telephone, departement, poste):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                UPDATE employees SET
                    nom=%s, prenom=%s, email=%s, telephone=%s,
                    departement=%s, poste=%s, updated_at=NOW()
                WHERE id=%s
            """, (nom, prenom, email, telephone, departement, poste, employe_id))
            con.commit()
            return True
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def supprimer_employe(self, employe_id):
        import datetime
        today = datetime.date.today().isoformat()
        con, cursor = self.db_tools.find_connection()
        try:
            con.autocommit(False)
            cursor.execute("""
                UPDATE car_assignments SET end_date = %s
                WHERE employee_id = %s AND end_date IS NULL
            """, (today, employe_id))
            cursor.execute("""
                UPDATE employees SET status = 'inactive' WHERE id = %s
            """, (employe_id,))
            con.commit()
            return True
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def get_affectation_active(self, employe_id):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                SELECT ca.id, ca.start_date,
                       c.id AS car_id, c.plate_number, cg.model
                FROM car_assignments ca
                JOIN cars c ON ca.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE ca.employee_id = %s AND ca.end_date IS NULL
            """, (employe_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            con.close()

    def get_profil_employe(self, employe_id):
        con, cursor = self.db_tools.find_connection()
        try:
            # employee info
            cursor.execute("""
                SELECT id, nom, prenom, departement, poste, email,
                       telephone, status, created_at, updated_at
                FROM employees WHERE id = %s
            """, (employe_id,))
            emp = cursor.fetchone()
            if not emp:
                return None

            # full assignment history
            cursor.execute("""
                SELECT ca.id, ca.car_id, ca.start_date, ca.end_date, ca.notes,
                       c.plate_number, c.brand, c.status AS car_status,
                       cg.model, cg.year,
                       DATEDIFF(COALESCE(ca.end_date, CURDATE()), ca.start_date) AS duree_jours
                FROM car_assignments ca
                JOIN cars c ON ca.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE ca.employee_id = %s
                ORDER BY ca.start_date DESC
            """, (employe_id,))
            assignments = [dict(r) for r in cursor.fetchall()]

            # sinistres involved in
            cursor.execute("""
                SELECT s.id, s.car_id, s.date_sinistre, s.type,
                       s.description, s.status, s.montant_reparation,
                       c.plate_number, cg.model
                FROM sinistres s
                JOIN cars c ON s.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE s.employee_id = %s
                ORDER BY s.date_sinistre DESC
            """, (employe_id,))
            sinistres = [dict(r) for r in cursor.fetchall()]

            return {
                'employe': dict(emp),
                'assignments': assignments,
                'sinistres': sinistres
            }
        finally:
            con.close()