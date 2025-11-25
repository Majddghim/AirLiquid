from tools.database_tools import DatabaseTools
from entities.admin import Admin


class AdminService:
    def __init__(self):
        self.db_tools = DatabaseTools()

    def get_admin_by_email(self, email):
        con, cursor = self.db_tools.find_connection()
        query = "SELECT id, username, password_hash AS password, email FROM admins WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchall()
        if result:
            admin_data = result[0]
            return Admin(
                id=admin_data['id'],
                username=admin_data['username'],
                password=admin_data['password'],
                email=admin_data['email']
            )
        return None

    def get_employe_by_email(self, email):
        con, cursor = self.db_tools.find_connection()
        query = "SELECT id, first_name, last_name,email, pwd AS password, email FROM employees WHERE email = %s"
        cursor.execute(query, (email,))
        result = cursor.fetchall()
        if result:
            admin_data = result[0]
            return {
                'id': admin_data['id'],
                'username': admin_data['first_name'] + ' ' + admin_data['last_name'],
                'password': admin_data['password'],
                'email': admin_data['email']
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
        print(f"Password (hash): {admin.password}")
    else:
        print("❌ No admin found with that email.")
