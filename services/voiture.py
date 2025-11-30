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
        result = cursor.fetchall()
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

    def ajouter_carte_grise(self, model, year, plate_number, owner_name, chassis_number, status, registration_date,
                            expiration_date):
        con, cursor = self.db_tools.find_connection()
        query = """
        INSERT INTO carte_grise (model, year, plate_number, owner_name, chassis_number, status, registration_date, expiration_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query,
                       (model, year, plate_number, owner_name, chassis_number, status, registration_date,
                        expiration_date))
        con.commit()
        return cursor.lastrowid

    def ajouter_voiture(self, employee_id, carte_grise_id, acquisition_date, status, notes):
        con, cursor = self.db_tools.find_connection()
        query = """
        INSERT INTO cars (employee_id, carte_grise_id, acquisition_date, status, notes)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (employee_id, carte_grise_id, acquisition_date, status, notes))
        con.commit()
        return cursor.lastrowid

    def supprimer_voiture(self, voiture_id):
        con, cursor = self.db_tools.find_connection()
        query = "DELETE FROM cars WHERE id = %s"
        cursor.execute(query, (voiture_id,))
        con.commit()
        return cursor.rowcount

    def mettre_a_jour_statut_voiture(self, voiture_id, new_status):
        con, cursor = self.db_tools.find_connection()
        query = "UPDATE cars SET status = %s WHERE id = %s"
        cursor.execute(query, (new_status, voiture_id))
        con.commit()
        return cursor.rowcount

    def lister_voitures_par_employe(self, employee_id):
        con, cursor = self.db_tools.find_connection()
        query = """
        SELECT c.id AS car_id, c.employee_id, c.carte_grise_id, c.acquisition_date, c.status, c.notes,
               cg.model, cg.year, cg.plate_number, cg.owner_name, cg.chassis_number, cg.registration_date, cg.expiration_date
        FROM cars c
        JOIN carte_grises cg ON c.carte_grise_id = cg.id
        WHERE c.employee_id = %s
        """
        cursor.execute(query, (employee_id,))
        result = cursor.fetchall()
        voitures = []
        for voiture_data in result:
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
            voiture = Car(
                id=voiture_data['car_id'],
                employee_id=voiture_data['employee_id'],
                carte_grise_id=carte_grise,
                acquisition_date=voiture_data['acquisition_date'],
                status=voiture_data['status'],
                notes=voiture_data['notes']
            )
            voitures.append(voiture)
        return voitures

    def get_all_voitures(self):
        con, cursor = self.db_tools.find_connection()
        query = """
        SELECT c.id AS car_id, c.employee_id, c.carte_grise_id, c.acquisition_date, c.status, c.notes,
               cg.model, cg.year, cg.plate_number, cg.owner_name, cg.chassis_number, cg.registration_date, cg.expiration_date
        FROM cars c
        JOIN carte_grises cg ON c.carte_grise_id = cg.id
        """
        cursor.execute(query)
        result = cursor.fetchall()
        voitures = []
        for voiture_data in result:
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
            voiture = Car(
                id=voiture_data['car_id'],
                employee_id=voiture_data['employee_id'],
                carte_grise_id=carte_grise,
                acquisition_date=voiture_data['acquisition_date'],
                status=voiture_data['status'],
                notes=voiture_data['notes']
            )
            voitures.append(voiture)
        return voitures

    def get_all_carte_grises(self):
        con, cursor = self.db_tools.find_connection()
        query = "SELECT id, model, year, plate_number, owner_name, chassis_number, registration_date, expiration_date FROM carte_grise"
        cursor.execute(query)
        result = cursor.fetchall()
        cartes_grises = []
        for cg_data in result:
            carte_grise = Carte_grise(
                id=cg_data['id'],
                model=cg_data['model'],
                year=cg_data['year'],
                plate_number=cg_data['plate_number'],
                owner_name=cg_data['owner_name'],
                chassis_number=cg_data['chassis_number'],
                registration_date=cg_data['registration_date'],
                expiration_date=cg_data['expiration_date']
            )
            cartes_grises.append(carte_grise)
        return cartes_grises

    def get_carte_grise_by_owner_name(self, owner_name):
        con, cursor = self.db_tools.find_connection()
        query = (f"SELECT id, model, `year`, plate_number, owner_name, chassis_number, registration_date, expiration_date, status"
                 f" FROM carte_grise WHERE id = '{owner_name}'")
        print(query)
        cursor.execute(query)
        result = cursor.fetchall()
        cartes_grises = []
        for cg_data in result:
            carte_grise = Carte_grise(
                id=cg_data['id'],
                model=cg_data['model'],
                year=cg_data['year'],
                status=cg_data['status'],
                plate_number=cg_data['plate_number'],
                owner_name=cg_data['owner_name'],
                chassis_number=cg_data['chassis_number'],
                registration_date=cg_data['registration_date'],
                expiration_date=cg_data['expiration_date']
            )
            cartes_grises.append(carte_grise)
        return cartes_grises
