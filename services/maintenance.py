from tools.database_tools import DatabaseTools
import datetime


class MaintenanceService:
    def __init__(self):
        self.db = DatabaseTools()

    # ------------------------------------------------------------------ #
    # ALERTS                                                               #
    # ------------------------------------------------------------------ #

    def get_alerts_by_car(self, car_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT ma.id, ma.car_id, ma.part_id, ma.alert_type,
                       ma.due_date, ma.due_km, ma.status, ma.created_at,
                       cp.name AS part_name, cp.category
                FROM maintenance_alerts ma
                JOIN car_parts cp ON ma.part_id = cp.id
                WHERE ma.car_id = %s AND ma.status = 'open'
                ORDER BY ma.due_date ASC
            """, (car_id,))
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()

    def get_all_open_alerts(self):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT ma.id, ma.car_id, ma.part_id, ma.alert_type,
                       ma.due_date, ma.due_km, ma.status, ma.created_at,
                       cp.name AS part_name, cp.category,
                       c.plate_number, cg.model
                FROM maintenance_alerts ma
                JOIN car_parts cp ON ma.part_id = cp.id
                JOIN cars c ON ma.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE ma.status = 'open'
                ORDER BY ma.due_date ASC
            """)
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()

    def close_alert(self, alert_id, cursor):
        cursor.execute("""
            UPDATE maintenance_alerts SET status = 'closed'
            WHERE id = %s
        """, (alert_id,))

    def create_alert(self, car_id, part_id, alert_type, due_date=None, due_km=None):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                INSERT INTO maintenance_alerts
                    (car_id, part_id, alert_type, due_date, due_km, status)
                VALUES (%s, %s, %s, %s, %s, 'open')
            """, (car_id, part_id, alert_type, due_date or None, due_km or None))
            con.commit()
            return cursor.lastrowid
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # RECORDS                                                              #
    # ------------------------------------------------------------------ #

    def get_records_by_car(self, car_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT mr.id, mr.car_id, mr.part_id, mr.garage_id,
                       mr.done_at, mr.km_at_service, mr.next_due_date,
                       mr.next_due_km, mr.status, mr.notes, mr.created_at,
                       cp.name AS part_name, cp.category,
                       g.name  AS garage_name,
                       f.id    AS facture_id, f.montant_ttc, f.file_path AS facture_file
                FROM maintenance_records mr
                JOIN car_parts cp ON mr.part_id = cp.id
                LEFT JOIN garages g ON mr.garage_id = g.id
                LEFT JOIN factures f ON f.type = 'maintenance' AND f.reference_id = mr.id
                WHERE mr.car_id = %s
                ORDER BY mr.done_at DESC
            """, (car_id,))
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()

    def log_maintenance(self, car_id, part_id, garage_id, done_at, km_at_service,
                        next_due_date, next_due_km, notes, alert_id=None):
        con, cursor = self.db.find_connection()
        try:
            con.autocommit(False)
            cursor.execute("""
                INSERT INTO maintenance_records
                    (car_id, part_id, garage_id, done_at, km_at_service,
                     next_due_date, next_due_km, status, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'done', %s)
            """, (
                car_id, part_id, garage_id or None,
                done_at, km_at_service or None,
                next_due_date or None, next_due_km or None,
                notes or None
            ))
            record_id = cursor.lastrowid

            # close the alert if one was linked
            if alert_id:
                self.close_alert(alert_id, cursor)

            # if next due date or km provided, create new alert
            if next_due_date or next_due_km:
                alert_type = 'both' if (next_due_date and next_due_km) else ('date' if next_due_date else 'km')
                cursor.execute("""
                    INSERT INTO maintenance_alerts
                        (car_id, part_id, alert_type, due_date, due_km, status)
                    VALUES (%s, %s, %s, %s, %s, 'open')
                """, (car_id, part_id, alert_type, next_due_date or None, next_due_km or None))

            con.commit()
            return record_id
        except Exception as e:
            con.rollback()
            raise e
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # FACTURES                                                             #
    # ------------------------------------------------------------------ #

    def get_facture_by_record(self, record_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT id, num_facture, num_reglement, date_facture,
                       date_reglement, montant_ht, montant_ttc, tva, file_path
                FROM factures
                WHERE type = 'maintenance' AND reference_id = %s
            """, (record_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            con.close()

    def attach_facture(self, record_id, car_id, num_facture, num_reglement,
                       date_facture, date_reglement, montant_ht, montant_ttc,
                       tva, file_path=None):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                INSERT INTO factures
                    (type, reference_id, car_id, num_facture, num_reglement,
                     date_facture, date_reglement, montant_ht, montant_ttc,
                     tva, file_path, extraction_status)
                VALUES ('maintenance', %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'verified')
            """, (
                record_id, car_id,
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

    # ------------------------------------------------------------------ #
    # BON DE COMMANDE DATA                                                 #
    # ------------------------------------------------------------------ #

    def get_bon_data(self, car_id):
        """Returns everything needed to build the bon de commande modal"""
        con, cursor = self.db.find_connection()
        try:
            # car info
            cursor.execute("""
                SELECT c.id, c.plate_number, c.brand,
                       cg.model, cg.year, cg.owner_name
                FROM cars c
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE c.id = %s
            """, (car_id,))
            car = cursor.fetchone()

            # open alerts
            cursor.execute("""
                SELECT ma.id, ma.part_id, ma.alert_type,
                       ma.due_date, ma.due_km,
                       cp.name AS part_name, cp.category
                FROM maintenance_alerts ma
                JOIN car_parts cp ON ma.part_id = cp.id
                WHERE ma.car_id = %s AND ma.status = 'open'
                ORDER BY ma.due_date ASC
            """, (car_id,))
            alerts = [dict(r) for r in cursor.fetchall()]

            # all parts for free-add
            cursor.execute("""
                SELECT id, name, category
                FROM car_parts ORDER BY category ASC, name ASC
            """)
            parts = [dict(r) for r in cursor.fetchall()]

            # active garages
            cursor.execute("""
                SELECT id, name, type, phone, address, contact_person
                FROM garages WHERE status = 'active' ORDER BY name ASC
            """)
            garages = [dict(r) for r in cursor.fetchall()]

            return {
                'car':     dict(car) if car else None,
                'alerts':  alerts,
                'parts':   parts,
                'garages': garages
            }
        finally:
            con.close()