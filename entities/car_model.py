class CarModel:
    def __init__(self,id,brand_id , name):
        self.id = id
        self.rband_id = brand_id
        self.name = name

    def to_dict(self):
        return {
            'id': self.id,
            'brand_id': self.rband_id,
            'name': self.name
        }