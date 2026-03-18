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

    def delete_employe(self, id):
        con, cursor = self.db_tools.find_connection()
        query = "DELETE FROM employees WHERE id = %s"
        cursor.execute(query, (id,))
        con.commit()
        con.close()
        return True

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
