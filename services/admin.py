from tools.database_tools import DatabaseTools
from entities.admin import Admin


class AdminService:
    def __init__(self):
        self.db_tools = DatabaseTools()

    def get_admin_by_email(self, email):
        con, cursor = self.db_tools.find_connection()
        query = "SELECT id, username, email, password_hash, status, created_at FROM admins WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchall()
        con.close()
        if result:
            admin_data = result[0]
            return Admin(
                id=admin_data['id'],
                username=admin_data['username'],
                email=admin_data['email'],
                password_hash=admin_data['password_hash'],
                status=admin_data['status'],
                created_at=admin_data['created_at']
            )
        return None

    def get_employe_by_email(self, email):
        con, cursor = self.db_tools.find_connection()
        # Note: New schema doesn't have a password field for employees. 
        # Using placeholder or adjusting if needed.
        query = "SELECT id, nom, prenom, email, telephone, poste, departement, status FROM employees WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchall()
        con.close()
        if result:
            emp_data = result[0]
            return {
                'id': emp_data['id'],
                'username': emp_data['prenom'] + ' ' + emp_data['nom'],
                'email': emp_data['email'],
                'telephone': emp_data['telephone'],
                'poste': emp_data['poste'],
                'departement': emp_data['departement'],
                'status': emp_data['status']
            }

        return None


# ✅ Testing the method
if __name__ == '__main__':
    admin_service = AdminService()
    admin = admin_service.get_admin_by_email('medbensaleh@gmail.com')

    if admin:
        print("✅ Admin found:")
        print(f"ID: {admin.id}")
        print(f"Username: {admin.username}")
        print(f"Email: {admin.email}")
    else:
        print("❌ No admin found with that email.")
