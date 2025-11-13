from tools.database_tools import DatabaseTools
from entities.car import Car
from entities.carte_grise import Carte_grise

class VoitureService:
    def __init__(self):
        self.db_tools = DatabaseTools()

    def get_voiture_by_id(self, voiture_id):
        con, cursor = self.db_tools.find_connection()
        query = """
        SELECT c.id AS car_id, c.employee_id, c.carte_grise_id, c.acquisition_date, c.status, c.notes,
               cg.model, cg.year, cg.plate_number, cg.owner_name, cg.chassis_number, cg.registration_date, cg.expiration_date
        FROM cars c
        JOIN carte_grises cg ON c.carte_grise_id = cg.id
        WHERE c.id = %s
        """
        cursor.execute(query, (voiture_id,))
        result  = cursor.fetchall()
        if result:
            voiture_data = result[0]
            carte_grise = Carte_grise(
                id=voiture_data['carte_grise_id'],
                model=voiture_data['model'],
                year=voiture_data['year'],
                plate_number=voiture_data['plate_number'],
                owner_name=voiture_data['owner_name'],
                chassis_number=voiture_data['chassis_number'],
                registration_date=voiture_data['registration_date'],
                expiration_date=voiture_data['expiration_date']
            )
            return Car(
                id=voiture_data['car_id'],
                employee_id=voiture_data['employee_id'],
                carte_grise_id=carte_grise,
                acquisition_date=voiture_data['acquisition_date'],
                status=voiture_data['status'],
                notes=voiture_data['notes']
            )
        return None