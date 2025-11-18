from tools.database_tools import DatabaseTools
from entities.employe import Employe


class EmployeService:
    def __init__(self):
        self.db_tools = DatabaseTools()

    def get_employe_by_something(self, condition, order='', limit='', dict_form=True):
        con, cursor = self.db_tools.find_connection()
        query = f"""SELECT id, first_name, last_name, department, position, email, phone, created_at FROM employees WHERE {condition} {order} {limit} """
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
        print(result)
        le = []
        if result:
             for employe_data in result:
                 e = Employe(
                     id=employe_data['id'],
                     first_name=employe_data['first_name'],
                     last_name=employe_data['last_name'],
                     department=employe_data['department'],
                     position=employe_data['position'],
                     email=employe_data['email'],
                     phone=employe_data['phone'],
                     created_at=employe_data['created_at'])
                 if dict_form:
                     le.append(e.__dict__())
                 else:
                    le.append(e)
             return le
        return None

    def get_employe_by_email(self, email):
        return self.get_employe_by_something(f" email = '{email}' ")

    def get_employe_by_id(self, id):
        con, cursor = self.db_tools.find_connection()
        query = "SELECT id, first_name, last_name, department, position, email, phone, created_at FROM employees WHERE id = %s"
        cursor.execute(query, (id,))
        result = cursor.fetchall()
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
        return self.get_employe_by_something(" 1=1 ")

    def add_employe(self, first_name, last_name, department, position, email, phone, created_at):
        con, cursor = self.db_tools.find_connection()
        query = """
        INSERT INTO employees (first_name, last_name, department, position, email, phone, created_at)
        VALUES (%s, %s, %s, %s, %s, %s,%s)
        """
        cursor.execute(query, (first_name, last_name, department, position, email, phone, created_at))
        con.commit()
        return cursor.lastrowid

    def get_employe_by_name(self, search_by_name, number=None, begin=None, dict_form=True):
        limit = ''
        if number is not None and begin is not None:
            limit = f"LIMIT {str(begin)}, {str(number)}"
        count = self.get_count_employe_something(
            f"( first_name LIKE '%{search_by_name}%' OR last_name LIKE '%{search_by_name}%' )")
        print(count)
        return self.get_employe_by_something(
            f"( first_name LIKE '%{search_by_name}%' OR last_name LIKE '%{search_by_name}%' )", limit=limit,
            dict_form=dict_form), count[1]['num']

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
            print('data count:', data)
            if not data:
                return 'failed', 'No employe found'
            return 'success', data
        except Exception as e:
            return 'failed', str(e)
