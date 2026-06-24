import os
import pymysql
from dotenv import load_dotenv

load_dotenv()


class DatabaseTools:
    def __init__(self):
        self.hostname = os.getenv('DB_HOST', 'localhost')
        self.user = os.getenv('DB_USER', 'root')
        self.pwd = os.getenv('DB_PASSWORD', '')
        self.db = os.getenv('DB_NAME', 'airliquide_flotte')
        self.port = int(os.getenv('DB_PORT', 3306))

    def find_connection(self):
        conn = pymysql.connect(
            host=self.hostname,
            port=self.port,
            user=self.user,
            password=self.pwd,
            database=self.db,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn, conn.cursor()

    def execute_request(self, request):
        connection = None
        try:
            connection, cursor = self.find_connection()
            cursor.execute(request)
            connection.commit()
            cursor.close()
            connection.close()
            return 'success'
        except Exception as e:
            if connection:
                connection.close()
            return 'error', e

    def test_connection(self):
        try:
            connection, cursor = self.find_connection()
            cursor.close()
            connection.close()
            return True
        except Exception as e:
            print("Connection failed:", e)
            return False


if __name__ == '__main__':
    db = DatabaseTools()
    db.test_connection()
