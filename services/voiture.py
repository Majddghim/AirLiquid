from tools.database_tools import DatabaseTools
from entities.car import Car
from entities.carte_grise import Carte_grise


class VoitureService:
    def __init__(self):
        self.db_tools = DatabaseTools()

    def get_voiture_by_id(self, voiture_id):
        con, cursor = self.db_tools.find_connection()
        query = """
        SELECT c.id, c.status, c.acquisition_date, c.notes, c.created_at, c.updated_at,
               cg.model, cg.year, cg.plate_number, cg.owner_name, cg.chassis_number, 
               cg.registration_date, cg.expiration_date, cg.file_path
        FROM cars c
        LEFT JOIN carte_grises cg ON c.id = cg.car_id
        WHERE c.id = %s
        """
        cursor.execute(query, (voiture_id,))
        result = cursor.fetchall()
        con.close()
        if result:
            data = result[0]
            # We return a flattened dict for the UI
            return data
        return None

    def check_plate_exists(self, plate_number):
        con, cursor = self.db_tools.find_connection()
        try:
            query = "SELECT car_id FROM carte_grises WHERE plate_number = %s"
            cursor.execute(query, (plate_number,))
            result = cursor.fetchone()
            return result is not None
        finally:
            con.close()

    def ajouter_voiture(self, model, year, plate_number, owner_name, chassis_number, status, 
                        registration_date, expiration_date, acquisition_date, notes, file_path=None):
        
        # 0. Check for duplicate plate before doing anything
        if self.check_plate_exists(plate_number):
            raise Exception(f"Une voiture avec le matricule '{plate_number}' existe déjà.")

        # Sanitize inputs: convert empty strings to None for optional SQL fields
        registration_date = registration_date if registration_date else None
        expiration_date = expiration_date if expiration_date else None
        acquisition_date = acquisition_date if acquisition_date else None
        year = int(year) if year else 0

        con, cursor = self.db_tools.find_connection()
        try:
            # Disable autocommit to ensure real transaction
            con.autocommit(False)
            
            # 1. Insert into cars
            query_car = """
            INSERT INTO cars (status, acquisition_date, notes)
            VALUES (%s, %s, %s)
            """
            cursor.execute(query_car, (status, acquisition_date, notes))
            car_id = cursor.lastrowid

            # 2. Insert into carte_grises
            query_cg = """
            INSERT INTO carte_grises (car_id, model, year, plate_number, owner_name, chassis_number, 
                                     registration_date, expiration_date, file_path)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_cg, (car_id, model, year, plate_number, owner_name, chassis_number, 
                                     registration_date, expiration_date, file_path))
            
            con.commit()
            return car_id
        except Exception as e:
            con.rollback()
            print(f"Transaction Error: {e}")
            raise e
        finally:
            con.close()



    def supprimer_voiture(self, voiture_id):
        con, cursor = self.db_tools.find_connection()
        # cascades should handle carte_grises and car_assignments
        query = "DELETE FROM cars WHERE id = %s"
        cursor.execute(query, (voiture_id,))
        con.commit()
        count = cursor.rowcount
        con.close()
        return count

    def mettre_a_jour_statut_voiture(self, voiture_id, new_status):
        con, cursor = self.db_tools.find_connection()
        query = "UPDATE cars SET status = %s WHERE id = %s"
        cursor.execute(query, (new_status, voiture_id))
        con.commit()
        count = cursor.rowcount
        con.close()
        return count

    def get_all_voitures(self):
        con, cursor = self.db_tools.find_connection()
        query = """
        SELECT c.id, c.status, c.acquisition_date, c.notes, c.created_at, c.updated_at,
               cg.model, cg.year, cg.plate_number, cg.owner_name, cg.chassis_number, 
               cg.registration_date, cg.expiration_date
        FROM cars c
        LEFT JOIN carte_grises cg ON c.id = cg.car_id
        """
        cursor.execute(query)
        result = cursor.fetchall()
        con.close()
        return result if result else []

    def get_voitures_paginated(self, search_by_name='', limit=10, offset=0):
        con, cursor = self.db_tools.find_connection()
        condition = "1=1"
        params = []
        if search_by_name:
            condition = "(cg.model LIKE %s OR cg.plate_number LIKE %s OR cg.owner_name LIKE %s)"
            search_param = f"%{search_by_name}%"
            params.extend([search_param, search_param, search_param])
        
        query = f"""
        SELECT c.id, c.status, c.acquisition_date, c.notes, c.created_at, c.updated_at,
               cg.model, cg.year, cg.plate_number, cg.owner_name, cg.chassis_number, 
               cg.registration_date, cg.expiration_date
        FROM cars c
        LEFT JOIN carte_grises cg ON c.id = cg.car_id
        WHERE {condition}
        ORDER BY c.created_at DESC
        LIMIT %s OFFSET %s
        """
        params.extend([limit, offset])
        
        cursor.execute(query, tuple(params))
        result = cursor.fetchall()
        
        # Count query
        count_query = f"""
        SELECT COUNT(c.id) as total
        FROM cars c
        LEFT JOIN carte_grises cg ON c.id = cg.car_id
        WHERE {condition}
        """
        cursor.execute(count_query, tuple(params[:-2]))
        total_count = cursor.fetchone()['total']
        
        con.close()
        return result if result else [], total_count

    def lister_voitures_par_employe(self, employee_id):
        con, cursor = self.db_tools.find_connection()
        query = """
        SELECT c.id, c.status, c.acquisition_date, c.notes, c.created_at, c.updated_at,
               cg.model, cg.year, cg.plate_number, cg.owner_name, cg.chassis_number, 
               cg.registration_date, cg.expiration_date
        FROM cars c
        JOIN car_assignments ca ON c.id = ca.car_id
        LEFT JOIN carte_grises cg ON c.id = cg.car_id
        WHERE ca.employee_id = %s AND ca.end_date IS NULL
        """
        cursor.execute(query, (employee_id,))
        result = cursor.fetchall()
        con.close()
        return result if result else []
