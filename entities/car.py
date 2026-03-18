class Car:
    def __init__(self, id, status='active', acquisition_date=None, notes=None, 
                 created_at=None, updated_at=None):
        self.id = id
        self.status = status
        self.acquisition_date = acquisition_date
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    def __dict__(self):
        return {
            'id': self.id,
            'status': self.status,
            'acquisition_date': self.acquisition_date,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }