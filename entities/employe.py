class Employe:
    def __init__(self, id, nom, prenom, email, telephone, poste, departement, status='active', created_at=None, updated_at=None):
        self.id = id
        self.nom = nom
        self.prenom = prenom
        self.email = email
        self.telephone = telephone
        self.poste = poste
        self.departement = departement
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def __dict__(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "prenom": self.prenom,
            "email": self.email,
            "telephone": self.telephone,
            "poste": self.poste,
            "departement": self.departement,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }