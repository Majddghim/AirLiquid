from tools.database_tools import DatabaseTools
import datetime


class SinistreService:
    def __init__(self):
        self.db = DatabaseTools()

    # ------------------------------------------------------------------ #
    # SINISTRES                                                            #
    # ------------------------------------------------------------------ #

    def get_sinistres_by_car(self, car_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT s.id, s.car_id, s.employee_id, s.date_sinistre,
                       s.type, s.description, s.n_constat, s.date_constat,
                       s.file_path, s.montant_reparation, s.mode_reglement,
                       s.n_cheque_or_virement, s.date_reglement, s.status,
                       s.created_at,
                       e.nom, e.prenom, e.poste,
                       f.id AS facture_id, f.montant_ttc, f.file_path AS facture_file
                FROM sinistres s
                LEFT JOIN employees e ON s.employee_id = e.id
                LEFT JOIN factures f ON f.type = 'sinistre' AND f.reference_id = s.id
                WHERE s.car_id = %s
                ORDER BY s.date_sinistre DESC
            """, (car_id,))
            rows = [dict(r) for r in cursor.fetchall()]
            # add replacement car info separately for each sinistre
            for row in rows:
                cursor.execute("""
                    SELECT c.id AS replacement_car_id, c.plate_number AS replacement_plate
                    FROM car_assignments ca
                    JOIN cars c ON ca.car_id = c.id
                    WHERE ca.employee_id = %s
                      AND ca.notes LIKE %s
                      AND ca.end_date IS NULL
                """, (row['employee_id'], f"Remplacement sinistre #{row['id']}%"))
                rep = cursor.fetchone()
                row['replacement_car_id'] = rep['replacement_car_id'] if rep else None
                row['replacement_plate'] = rep['replacement_plate'] if rep else None
            return rows
        finally:
            con.close()

    def get_sinistre_by_id(self, sinistre_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT s.*, e.nom, e.prenom, e.poste,
                       f.id AS facture_id, f.montant_ttc, f.file_path AS facture_file
                FROM sinistres s
                LEFT JOIN employees e ON s.employee_id = e.id
                LEFT JOIN factures f ON f.type = 'sinistre' AND f.reference_id = s.id
                WHERE s.id = %s
            """, (sinistre_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            con.close()

    def declarer_sinistre(self, car_id, employee_id, date_sinistre, type_sinistre,
                          description, n_constat, date_constat, file_path,
                          set_maintenance, prise_en_charge,
                          replacement_car_id=None):
        today = datetime.date.today().isoformat()
        con, cursor = self.db.find_connection()
        try:
            con.autocommit(False)

            # insert sinistre
            cursor.execute("""
                INSERT INTO sinistres
                    (car_id, employee_id, date_sinistre, type, description,
                     n_constat, date_constat, file_path, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'ouvert')
            """, (
                car_id, employee_id or None,
                date_sinistre, type_sinistre,
                description or None, n_constat or None,
                date_constat or None, file_path or None
            ))
            sinistre_id = cursor.lastrowid

            # set car to maintenance if requested
            if set_maintenance:
                cursor.execute("""
                    UPDATE cars SET status = 'maintenance' WHERE id = %s
                """, (car_id,))

            # assign replacement car if provided
            if replacement_car_id:
                # close current assignment of original car for this employee
                cursor.execute("""
                    UPDATE car_assignments SET end_date = %s
                    WHERE car_id = %s AND employee_id = %s AND end_date IS NULL
                """, (today, car_id, employee_id))

                # assign replacement car
                cursor.execute("""
                    INSERT INTO car_assignments
                        (car_id, employee_id, start_date, notes)
                    VALUES (%s, %s, %s, %s)
                """, (
                    replacement_car_id, employee_id, today,
                    f'Remplacement sinistre #{sinistre_id} — véhicule original en maintenance'
                ))

            con.commit()
            return sinistre_id
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def update_sinistre_status(self, sinistre_id, status):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                UPDATE sinistres SET status = %s WHERE id = %s
            """, (status, sinistre_id))
            con.commit()
        finally:
            con.close()

    def cloturer_sinistre(self, sinistre_id, car_id, employee_id,
                          montant_reparation, mode_reglement,
                          n_cheque_or_virement, date_reglement,
                          retourner_vehicule, replacement_car_id=None):
        today = datetime.date.today().isoformat()
        con, cursor = self.db.find_connection()
        try:
            con.autocommit(False)

            cursor.execute("""
                UPDATE sinistres SET
                    status = 'cloture',
                    montant_reparation = %s,
                    mode_reglement = %s,
                    n_cheque_or_virement = %s,
                    date_reglement = %s
                WHERE id = %s
            """, (
                montant_reparation or None,
                mode_reglement or None,
                n_cheque_or_virement or None,
                date_reglement or None,
                sinistre_id
            ))

            cursor.execute("UPDATE cars SET status = 'active' WHERE id = %s", (car_id,))

            if retourner_vehicule and employee_id:
                if replacement_car_id:
                    cursor.execute("""
                        UPDATE car_assignments SET end_date = %s
                        WHERE car_id = %s AND employee_id = %s AND end_date IS NULL
                    """, (today, replacement_car_id, employee_id))

                cursor.execute("""
                    INSERT INTO car_assignments
                        (car_id, employee_id, start_date, notes)
                    VALUES (%s, %s, %s, %s)
                """, (
                    car_id, employee_id, today,
                    f'Retour véhicule après sinistre #{sinistre_id}'
                ))

            con.commit()
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # FACTURES                                                             #
    # ------------------------------------------------------------------ #

    def attach_facture(self, sinistre_id, car_id, num_facture, num_reglement,
                       date_facture, date_reglement, montant_ht, montant_ttc,
                       tva, prise_en_charge, file_path=None):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                INSERT INTO factures
                    (type, reference_id, car_id, num_facture, num_reglement,
                     date_facture, date_reglement, montant_ht, montant_ttc,
                     tva, file_path, extraction_status)
                VALUES ('sinistre', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'verified')
            """, (
                sinistre_id, car_id,
                num_facture or None, num_reglement or None,
                date_facture or None, date_reglement or None,
                montant_ht or None, montant_ttc or None,
                tva or None, file_path or None
            ))
            con.commit()
            return cursor.lastrowid
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    def get_facture_by_sinistre(self, sinistre_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT id, num_facture, num_reglement, date_facture,
                       date_reglement, montant_ht, montant_ttc, tva, file_path
                FROM factures
                WHERE type = 'sinistre' AND reference_id = %s
            """, (sinistre_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # HELPERS                                                              #
    # ------------------------------------------------------------------ #

    def get_available_replacement_cars(self):
        """Cars that are active and not currently assigned to anyone"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT c.id, c.plate_number, c.brand,
                       cg.model, cg.year
                FROM cars c
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                LEFT JOIN car_assignments ca ON ca.car_id = c.id AND ca.end_date IS NULL
                WHERE c.status = 'active'
                  AND ca.id IS NULL
                ORDER BY c.brand ASC
            """)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()

    def get_all_sinistres(self):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT s.id, s.car_id, s.date_sinistre, s.type,
                       s.description, s.status, s.montant_reparation,
                       e.nom, e.prenom,
                       c.plate_number, cg.model
                FROM sinistres s
                LEFT JOIN employees e ON s.employee_id = e.id
                JOIN cars c ON s.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                ORDER BY s.date_sinistre DESC
            """)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()