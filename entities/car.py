class Car:
    def __init__(self, id, plate_number=None, brand=None, current_cg_id=None,
                 status='active', acquisition_date=None, notes=None,
                 created_at=None, updated_at=None):
        self.id = id
        self.plate_number = plate_number
        self.brand = brand
        self.current_cg_id = current_cg_id
        self.status = status
        self.acquisition_date = acquisition_date
        self.notes = notes
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'brand': self.brand,
            'current_cg_id': self.current_cg_id,
            'status': self.status,
            'acquisition_date': self.acquisition_date,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }