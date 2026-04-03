class Poste:
    def __init__(self, id, departement_id, name):
        self.id             = id
        self.departement_id = departement_id
        self.name           = name

    def __dict__(self):
        return {'id': self.id, 'departement_id': self.departement_id, 'name': self.name}