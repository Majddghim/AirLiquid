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