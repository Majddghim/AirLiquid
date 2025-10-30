import pymysql


class DatabaseTools:
                def __init__(self):
                    self.hostname = 'localhost'
                    self.user = 'root'
                    self.pwd = ''
                    self.db = 'parking'
                    self.port = 3306

                def find_connection(self):
                    conn = pymysql.connect(
                        host=self.hostname,
                        port=self.port,
                        user=self.user,
                        password=self.pwd,
                        database=self.db,
                        cursorclass=pymysql.cursors.DictCursor  # ✅ This ensures rows are returned as dictionaries
                    )
                    return conn, conn.cursor()

                def execute_request(self, request):
                    try:
                        connection, cursor = self.find_connection()
                        cursor.execute(request)
                        connection.commit()
                        cursor.close()
                        connection.close()
                        return 'success'
                    except Exception as e:
                        return 'error', e

                def test_connection(self):
                    try:
                        connection, cursor = self.find_connection()
                        print("Connection successful!")
                        cursor.close()
                        connection.close()
                    except Exception as e:
                        print("Connection failed:", e)


if __name__ == '__main__':
    db = DatabaseTools()
    db.test_connection()