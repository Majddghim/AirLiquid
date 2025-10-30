class Admin:
    def __init__(self, id, username, password, email):
        self.id = id
        self.username = username
        self.password = password
        self.email = email

    def __dict__(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email
        }
