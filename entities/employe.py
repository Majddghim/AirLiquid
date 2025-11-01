class Employe:
    def __init__(self, id , first_name , last_name , department , position , email, phone , created_at):
        self.id = id
        self.first_name = first_name
        self.last_name = last_name
        self.department = department
        self.position = position
        self.email = email
        self.phone = phone
        self.created_at = created_at

    def __dict__(self):
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "department": self.department,
            "position": self.position,
            "email": self.email,
            "phone": self.phone,
            "created_at": self.created_at
        }