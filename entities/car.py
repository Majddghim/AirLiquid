class Car :
    def __init__(self, id , employee_id, carte_grise_id, acquisition_date, status , notes ):
        self.id = id
        self.employee_id = employee_id
        self.carte_grise_id = carte_grise_id
        self.acquisition_date = acquisition_date
        self.status = status
        self.notes = notes

    def __dict__(self):
        return {
            'id': self.id,
            'employee_id': self.employee_id,
            'carte_grise_id': self.carte_grise_id,
            'acquisition_date': self.acquisition_date,
            'status': self.status,
            'notes': self.notes
        }