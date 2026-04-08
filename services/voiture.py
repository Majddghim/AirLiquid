from tools.database_tools import DatabaseTools
from entities.car import Car
from entities.carte_grise import Carte_grise


class VoitureService:
    def __init__(self):
        self.db_tools = DatabaseTools()

    # ------------------------------------------------------------------ #
    # EXISTING METHODS                                                     #
    # ------------------------------------------------------------------ #

    def get_voiture_by_id(self, voiture_id):
        con, cursor = self.db_tools.find_connection()
        cursor.execute("""
        SELECT c.id, c.plate_number, c.brand, c.current_cg_id,
               c.status, c.acquisition_date, c.notes, c.created_at, c.updated_at,
               cg.model, cg.year, cg.owner_name, cg.chassis_number,
               cg.puissance_fiscale, cg.carburant,
               cg.registration_date, cg.expiration_date, cg.file_path
        FROM cars c
        LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
        WHERE c.id = %s
        """, (voiture_id,))
        result = cursor.fetchone()
        con.close()
        return result

    def check_plate_exists(self, plate_number):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("SELECT id FROM cars WHERE plate_number = %s", (plate_number,))
            return cursor.fetchone() is not None
        finally:
            con.close()

    def ajouter_voiture(self, model, year, plate_number, owner_name, chassis_number, status,
                        registration_date, expiration_date, acquisition_date, notes, file_path=None):
        if self.check_plate_exists(plate_number):
            raise Exception(f"Une voiture avec le matricule '{plate_number}' existe déjà.")

        registration_date = registration_date or None
        expiration_date   = expiration_date   or None
        acquisition_date  = acquisition_date  or None
        year = int(year) if year else 0

        con, cursor = self.db_tools.find_connection()
        try:
            con.autocommit(False)
            brand = model.split()[0] if model else None
            cursor.execute("""
                INSERT INTO cars (plate_number, brand, status, acquisition_date, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (plate_number, brand, status, acquisition_date, notes))
            car_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO carte_grises (car_id, model, year, plate_number, owner_name,
                                          chassis_number, registration_date, expiration_date, file_path)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (car_id, model, year, plate_number, owner_name, chassis_number,
                  registration_date, expiration_date, file_path))
            cg_id = cursor.lastrowid
            cursor.execute("UPDATE cars SET current_cg_id = %s WHERE id = %s", (cg_id, car_id))
            con.commit()
            return car_id
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def supprimer_voiture(self, voiture_id):
        con, cursor = self.db_tools.find_connection()
        cursor.execute("DELETE FROM cars WHERE id = %s", (voiture_id,))
        con.commit()
        count = cursor.rowcount
        con.close()
        return count

    def mettre_a_jour_statut_voiture(self, voiture_id, new_status):
        con, cursor = self.db_tools.find_connection()
        cursor.execute("UPDATE cars SET status = %s WHERE id = %s", (new_status, voiture_id))
        con.commit()
        count = cursor.rowcount
        con.close()
        return count

    def get_all_voitures(self):
        con, cursor = self.db_tools.find_connection()
        cursor.execute("""
        SELECT
            c.id, c.plate_number, c.brand, c.status, c.acquisition_date,
            c.notes, c.created_at, c.updated_at,
            cg.model, cg.year, cg.owner_name, cg.chassis_number,
            cg.puissance_fiscale, cg.carburant,
            cg.registration_date, cg.expiration_date,
            CASE WHEN ins.car_id IS NOT NULL THEN 1 ELSE 0 END AS has_assurance,
            CASE WHEN vig.car_id IS NOT NULL THEN 1 ELSE 0 END AS has_vignette,
            CASE WHEN vt.car_id  IS NOT NULL THEN 1 ELSE 0 END AS has_visite
        FROM cars c
        LEFT JOIN carte_grises cg   ON c.current_cg_id = cg.id
        LEFT JOIN (SELECT DISTINCT car_id FROM insurances)        ins ON ins.car_id = c.id
        LEFT JOIN (SELECT DISTINCT car_id FROM vignettes)         vig ON vig.car_id = c.id
        LEFT JOIN (SELECT DISTINCT car_id FROM visite_technique)  vt  ON vt.car_id  = c.id
        """)
        rows = cursor.fetchall()
        con.close()

        result = []
        for row in rows:
            row = dict(row)
            row['dossier_complet'] = bool(
                row.pop('has_assurance') and
                row.pop('has_vignette')  and
                row.pop('has_visite')
            )
            result.append(row)
        return result

    def get_voitures_paginated(self, search_by_name='', limit=10, offset=0):
        con, cursor = self.db_tools.find_connection()
        condition = "1=1"
        params = []
        if search_by_name:
            condition = "(cg.model LIKE %s OR c.plate_number LIKE %s OR cg.owner_name LIKE %s)"
            s = f"%{search_by_name}%"
            params.extend([s, s, s])

        cursor.execute(f"""
        SELECT c.id, c.plate_number, c.brand, c.status, c.acquisition_date,
               c.notes, c.created_at, c.updated_at,
               cg.model, cg.year, cg.owner_name, cg.chassis_number,
               cg.puissance_fiscale, cg.carburant,
               cg.registration_date, cg.expiration_date
        FROM cars c
        LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
        WHERE {condition} ORDER BY c.created_at DESC LIMIT %s OFFSET %s
        """, tuple(params + [limit, offset]))
        result = cursor.fetchall()

        cursor.execute(f"""
        SELECT COUNT(c.id) as total FROM cars c
        LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id WHERE {condition}
        """, tuple(params))
        total = cursor.fetchone()['total']
        con.close()
        return result if result else [], total

    def lister_voitures_par_employe(self, employee_id):
        con, cursor = self.db_tools.find_connection()
        cursor.execute("""
        SELECT c.id, c.plate_number, c.brand, c.status, c.acquisition_date,
               c.notes, c.created_at, c.updated_at,
               cg.model, cg.year, cg.owner_name, cg.chassis_number,
               cg.registration_date, cg.expiration_date
        FROM cars c
        JOIN car_assignments ca ON c.id = ca.car_id
        LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
        WHERE ca.employee_id = %s AND ca.end_date IS NULL
        """, (employee_id,))
        result = cursor.fetchall()
        con.close()
        return result if result else []

    # ------------------------------------------------------------------ #
    # SCAN FLOW                                                            #
    # ------------------------------------------------------------------ #

    def save_temp_carte_grise(self, file_path, extracted_data):
        con, cursor = self.db_tools.find_connection()
        try:
            import json
            cursor.execute("""
                INSERT INTO carte_grises (
                    car_id, model, year, plate_number, owner_name, chassis_number,
                    puissance_fiscale, carburant, registration_date, expiration_date,
                    file_path, extraction_status, extracted_json
                ) VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s)
            """, (
                extracted_data.get('model'), extracted_data.get('year'),
                extracted_data.get('plate_number'), extracted_data.get('owner_name'),
                extracted_data.get('chassis_number'), extracted_data.get('puissance_fiscale'),
                extracted_data.get('carburant'), extracted_data.get('registration_date'),
                extracted_data.get('expiration_date'), file_path, json.dumps(extracted_data)
            ))
            con.commit()
            return cursor.lastrowid
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def get_pending_cg(self, cg_id):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                SELECT * FROM carte_grises
                WHERE id = %s AND car_id IS NULL AND extraction_status = 'pending'
            """, (cg_id,))
            return cursor.fetchone()
        finally:
            con.close()

    def confirm_car_creation(self, cg_id, form_data):
        plate_number      = form_data.get('plate_number', '').strip()
        brand             = form_data.get('brand', '').strip()
        status            = form_data.get('status', 'active')
        acquisition_date  = form_data.get('acquisition_date') or None
        notes             = form_data.get('notes') or None
        model             = form_data.get('model', '').strip()
        year              = int(form_data.get('year', 0)) if form_data.get('year') else None
        owner_name        = form_data.get('owner_name', '').strip()
        chassis_number    = form_data.get('chassis_number', '').strip()
        puissance_fiscale = form_data.get('puissance_fiscale') or None
        carburant         = form_data.get('carburant') or None
        registration_date = form_data.get('registration_date') or None
        expiration_date   = form_data.get('expiration_date') or None

        if self.check_plate_exists(plate_number):
            raise Exception(f"Une voiture avec le matricule '{plate_number}' existe déjà.")

        con, cursor = self.db_tools.find_connection()
        try:
            con.autocommit(False)
            cursor.execute("""
                INSERT INTO cars (plate_number, brand, status, acquisition_date, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (plate_number, brand, status, acquisition_date, notes))
            car_id = cursor.lastrowid

            cursor.execute("""
                UPDATE carte_grises SET
                    car_id=%s, model=%s, year=%s, plate_number=%s, owner_name=%s,
                    chassis_number=%s, puissance_fiscale=%s, carburant=%s,
                    registration_date=%s, expiration_date=%s, extraction_status='verified'
                WHERE id = %s
            """, (car_id, model, year, plate_number, owner_name, chassis_number,
                  puissance_fiscale, carburant, registration_date, expiration_date, cg_id))

            cursor.execute("UPDATE cars SET current_cg_id = %s WHERE id = %s", (cg_id, car_id))
            con.commit()
            return car_id
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # AFFECTATION                                                          #
    # ------------------------------------------------------------------ #

    def get_affectation_active(self, car_id):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                SELECT ca.id, ca.car_id, ca.employee_id, ca.start_date, ca.notes,
                       e.nom, e.prenom, e.poste, e.departement
                FROM car_assignments ca
                JOIN employees e ON ca.employee_id = e.id
                WHERE ca.car_id = %s AND ca.end_date IS NULL
            """, (car_id,))
            return cursor.fetchone()
        finally:
            con.close()

    def affecter_voiture(self, car_id, employee_id, start_date, admin_id, notes=None):
        import datetime
        today = datetime.date.today().isoformat()
        con, cursor = self.db_tools.find_connection()
        try:
            con.autocommit(False)
            cursor.execute("""
                UPDATE car_assignments SET end_date = %s
                WHERE car_id = %s AND end_date IS NULL
            """, (today, car_id))
            cursor.execute("""
                INSERT INTO car_assignments (car_id, employee_id, start_date, assigned_by_admin_id, notes)
                VALUES (%s, %s, %s, %s, %s)
            """, (car_id, employee_id, start_date, admin_id, notes or None))
            con.commit()
            return cursor.lastrowid
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # DOCUMENT METHODS                                                     #
    # ------------------------------------------------------------------ #

    def save_assurance(self, car_id, insurer, policy_number, start_date, end_date, file_path=None):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                INSERT INTO insurances (car_id, insurer, policy_number, start_date, end_date,
                                        status, file_path, extraction_status)
                VALUES (%s, %s, %s, %s, %s, 'active', %s, 'verified')
            """, (car_id, insurer, policy_number, start_date, end_date, file_path))
            con.commit()
            return cursor.lastrowid
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def save_vignette(self, car_id, year, expiration_date, montant=None, file_path=None):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                INSERT INTO vignettes (car_id, year, expiration_date, montant,
                                       status, file_path, extraction_status)
                VALUES (%s, %s, %s, %s, 'active', %s, 'verified')
            """, (car_id, year, expiration_date, montant or None, file_path))
            con.commit()
            return cursor.lastrowid
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def save_visite_technique(self, car_id, expiration_date, montant=None, file_path=None):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                INSERT INTO visite_technique (car_id, expiration_date, montant,
                                              status, file_path, extraction_status)
                VALUES (%s, %s, %s, 'active', %s, 'verified')
            """, (car_id, expiration_date, montant or None, file_path))
            con.commit()
            return cursor.lastrowid
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def get_brands(self):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("SELECT id, name FROM car_brands ORDER BY name ASC")
            return cursor.fetchall()
        finally:
            con.close()

    def get_models_by_brand(self, brand_id):
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute(
                "SELECT id, name FROM car_models WHERE brand_id = %s ORDER BY name ASC",
                (brand_id,)
            )
            return cursor.fetchall()
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # CAR DETAIL — fetches everything in one call                         #
    # ------------------------------------------------------------------ #

    def get_car_detail(self, car_id):
        """
        Returns a dict with:
        - car: all car + carte grise fields
        - documents: { assurance, vignette, visite } — most recent of each
        - affectation: current active assignment with employee info
        """
        con, cursor = self.db_tools.find_connection()
        try:
            # car + carte grise
            cursor.execute("""
                SELECT c.id, c.plate_number, c.brand, c.status,
                       c.acquisition_date, c.notes, c.created_at,
                       cg.model, cg.year, cg.owner_name, cg.chassis_number,
                       cg.puissance_fiscale, cg.carburant,
                       cg.registration_date, cg.expiration_date, cg.file_path AS cg_file
                FROM cars c
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE c.id = %s
            """, (car_id,))
            car = cursor.fetchone()
            if not car:
                return None

            # most recent assurance
            cursor.execute("""
                SELECT id, insurer, policy_number, start_date, end_date, status, file_path
                FROM insurances WHERE car_id = %s ORDER BY end_date DESC LIMIT 1
            """, (car_id,))
            assurance = cursor.fetchone()

            # most recent vignette
            cursor.execute("""
                SELECT id, year, expiration_date, montant, status, file_path
                FROM vignettes WHERE car_id = %s ORDER BY expiration_date DESC LIMIT 1
            """, (car_id,))
            vignette = cursor.fetchone()

            # most recent visite technique
            cursor.execute("""
                SELECT id, expiration_date, montant, status, file_path
                FROM visite_technique WHERE car_id = %s ORDER BY expiration_date DESC LIMIT 1
            """, (car_id,))
            visite = cursor.fetchone()

            # active affectation
            cursor.execute("""
                SELECT ca.start_date, ca.notes,
                       e.id AS employee_id, e.nom, e.prenom, e.poste, e.departement
                FROM car_assignments ca
                JOIN employees e ON ca.employee_id = e.id
                WHERE ca.car_id = %s AND ca.end_date IS NULL
            """, (car_id,))
            affectation = cursor.fetchone()

            return {
                'car':         dict(car),
                'documents': {
                    'assurance': dict(assurance) if assurance else None,
                    'vignette':  dict(vignette)  if vignette  else None,
                    'visite':    dict(visite)     if visite    else None,
                },
                'affectation': dict(affectation) if affectation else None,
            }
        finally:
            con.close()

    def supprimer_voiture(self, voiture_id):
        import datetime
        today = datetime.date.today().isoformat()
        con, cursor = self.db_tools.find_connection()
        try:
            con.autocommit(False)
            # close active assignment if exists — keeps history
            cursor.execute("""
                UPDATE car_assignments SET end_date = %s
                WHERE car_id = %s AND end_date IS NULL
            """, (today, voiture_id))
            # soft delete the car
            cursor.execute("""
                UPDATE cars SET status = 'retired' WHERE id = %s
            """, (voiture_id,))
            con.commit()
            return cursor.rowcount
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def update_voiture(self, car_id, brand, model, plate_number, year, owner_name,
                       chassis_number, puissance_fiscale, carburant,
                       registration_date, expiration_date, acquisition_date, status, notes):
        con, cursor = self.db_tools.find_connection()
        try:
            con.autocommit(False)
            cursor.execute("""
                UPDATE cars SET
                    plate_number = %s, brand = %s, status = %s,
                    acquisition_date = %s, notes = %s, updated_at = NOW()
                WHERE id = %s
            """, (plate_number, brand, status, acquisition_date or None, notes or None, car_id))

            cursor.execute("""
                UPDATE carte_grises SET
                    model = %s, year = %s, plate_number = %s, owner_name = %s,
                    chassis_number = %s, puissance_fiscale = %s, carburant = %s,
                    registration_date = %s, expiration_date = %s
                WHERE car_id = %s
            """, (model, year or None, plate_number, owner_name or None,
                  chassis_number or None, puissance_fiscale or None, carburant or None,
                  registration_date or None, expiration_date or None, car_id))

            con.commit()
            return True
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()