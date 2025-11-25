class Carte_grise:
    def __init__(self, id , model , year, plate_number , owner_name , chassis_number , registration_date , expiration_date):
        self.id = id
        self.model = model
        self.year = year
        self.plate_number = plate_number
        self.owner_name = owner_name
        self.chassis_number = chassis_number
        self.registration_date = registration_date
        self.expiration_date = expiration_date

    def __dict__(self):
        return {
            'id': self.id,

            'model': self.model,
            'year': self.year,
            'plate_number': self.plate_number,
            'owner_name': self.owner_name,
            'chassis_number': self.chassis_number,
            'registration_date': self.registration_date,
            'expiration_date': self.expiration_date
        }
