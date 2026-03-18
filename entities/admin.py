class Admin:
    def __init__(self, id, username, email, password_hash, status='active', created_at=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.status = status
        self.created_at = created_at

    def __dict__(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'password_hash': self.password_hash,
            'status': self.status,
            'created_at': self.created_at
        }
