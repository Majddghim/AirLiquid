class Departement:
    def __init__(self, id, name):
        self.id   = id
        self.name = name

    def __dict__(self):
        return {'id': self.id, 'name': self.name}