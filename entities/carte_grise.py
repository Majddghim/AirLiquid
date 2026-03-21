class Carte_grise:
    def __init__(self, id, car_id, model, year, plate_number, owner_name, chassis_number,
                 puissance_fiscale=None, carburant=None,
                 registration_date=None, expiration_date=None, file_path=None,
                 extraction_status='pending', extracted_json=None,
                 verified_by_admin_id=None, verified_at=None,
                 verification_notes=None, created_at=None, updated_at=None):
        self.id = id
        self.car_id = car_id
        self.model = model
        self.year = year
        self.plate_number = plate_number
        self.owner_name = owner_name
        self.chassis_number = chassis_number
        self.puissance_fiscale = puissance_fiscale
        self.carburant = carburant
        self.registration_date = registration_date
        self.expiration_date = expiration_date
        self.file_path = file_path
        self.extraction_status = extraction_status
        self.extracted_json = extracted_json
        self.verified_by_admin_id = verified_by_admin_id
        self.verified_at = verified_at
        self.verification_notes = verification_notes
        self.created_at = created_at
        self.updated_at = updated_at

    def to_dict(self):
        return {
            'id': self.id,
            'car_id': self.car_id,
            'model': self.model,
            'year': self.year,
            'plate_number': self.plate_number,
            'owner_name': self.owner_name,
            'chassis_number': self.chassis_number,
            'puissance_fiscale': self.puissance_fiscale,
            'carburant': self.carburant,
            'registration_date': self.registration_date,
            'expiration_date': self.expiration_date,
            'file_path': self.file_path,
            'extraction_status': self.extraction_status,
            'extracted_json': self.extracted_json,
            'verified_by_admin_id': self.verified_by_admin_id,
            'verified_at': self.verified_at,
            'verification_notes': self.verification_notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }