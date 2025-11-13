from tools.database_tools import DatabaseTools
from entities.employe import Employe

class EmployeService:
    def __init__(self):
        self.db_tools = DatabaseTools()

    def get_employe_by_email(self, email):
        con, cursor = self.db_tools.find_connection()
        query = "SELECT id, first_name, last_name, department, position, email, phone, created_at FROM employes WHERE email = %s"
        cursor.execute(query, (email,))
        result  = cursor.fetchall()
        if result:
            employe_data = result[0]
            return Employe(
                id=employe_data['id'],
                first_name=employe_data['first_name'],
                last_name=employe_data['last_name'],
                department=employe_data['department'],
                position=employe_data['position'],
                email=employe_data['email'],
                phone=employe_data['phone'],
                created_at=employe_data['created_at']
            )
        return None

    def get_employe_by_id(self, id):
        con, cursor = self.db_tools.find_connection()
        query = "SELECT id, first_name, last_name, department, position, email, phone, created_at FROM employes WHERE id = %s"
        cursor.execute(query, (id,))
        result  = cursor.fetchall()
        if result:
            employe_data = result[0]
            return Employe(
                id=employe_data['id'],
                first_name=employe_data['first_name'],
                last_name=employe_data['last_name'],
                department=employe_data['department'],
                position=employe_data['position'],
                email=employe_data['email'],
                phone=employe_data['phone'],
                created_at=employe_data['created_at']
            )
        return None

    def get_all_employes(self):
        con, cursor = self.db_tools.find_connection()
        query = "SELECT id, first_name, last_name, department, position, email, phone, created_at FROM employes"
        cursor.execute(query)
        results  = cursor.fetchall()
        employes = []
        for employe_data in results:
            employes.append(Employe(
                id=employe_data['id'],
                first_name=employe_data['first_name'],
                last_name=employe_data['last_name'],
                department=employe_data['department'],
                position=employe_data['position'],
                email=employe_data['email'],
                phone=employe_data['phone'],
                created_at=employe_data['created_at']
            ))
        return employes

    def add_employe(self, first_name, last_name, department, position, email, phone , created_at):
        con, cursor = self.db_tools.find_connection()
        query = """
        INSERT INTO employes (first_name, last_name, department, position, email, phone, created_at)
        VALUES (%s, %s, %s, %s, %s, %s,%s)
        """
        cursor.execute(query, (first_name, last_name, department, position, email, phone, created_at))
        con.commit()
        return cursor.lastrowid