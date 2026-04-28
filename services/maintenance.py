from tools.database_tools import DatabaseTools
import datetime


class MaintenanceService:
    def __init__(self):
        self.db = DatabaseTools()

    # ------------------------------------------------------------------ #
    # ALERTS                                                               #
    # ------------------------------------------------------------------ #

    def get_alerts_by_car(self, car_id, days_ahead=15):
        con, cursor = self.db.find_connection()
        try:
            # get current km for this car
            cursor.execute("""
                SELECT km FROM car_km
                WHERE car_id = %s ORDER BY recorded_at DESC, id DESC LIMIT 1
            """, (car_id,))
            km_row = cursor.fetchone()
            current_km = km_row['km'] if km_row else None

            cursor.execute("""
                SELECT ma.id, ma.car_id, ma.part_id, ma.alert_type,
                       ma.due_date, ma.due_km, ma.status, ma.created_at,
                       cp.name AS part_name, cp.category,
                       cp.alert_km_interval
                FROM maintenance_alerts ma
                JOIN car_parts cp ON ma.part_id = cp.id
                WHERE ma.car_id = %s
                  AND ma.status = 'open'
                ORDER BY ma.due_date ASC
            """, (car_id,))
            all_alerts = [dict(r) for r in cursor.fetchall()]

            result = []
            for alert in all_alerts:
                show = False
                alert_type = alert['alert_type']
                due_date = alert['due_date']
                due_km = alert['due_km']
                km_interval = alert['alert_km_interval']

                # date check — show if due within 15 days or overdue
                if due_date:
                    cursor.execute("""
                        SELECT DATEDIFF(%s, CURDATE()) AS days_left
                    """, (due_date,))
                    diff = cursor.fetchone()
                    days_left = diff['days_left'] if diff else None
                    if days_left is not None and days_left <= days_ahead:
                        show = True

                # km check — show if within 5% of interval or overdue
                if due_km and current_km is not None:
                    threshold = int(km_interval * 0.05) if km_interval else 500
                    if current_km >= due_km - threshold:
                        show = True

                # if no date and no km — always show
                if not due_date and not due_km:
                    show = True

                if show:
                    result.append(alert)

            return result
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

            # log km to car_km table if provided
            if km_at_service:
                cursor.execute("""
                    INSERT INTO car_km (car_id, km, recorded_at)
                    VALUES (%s, %s, %s)
                """, (car_id, km_at_service, done_at))

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

            # get current km
            cursor.execute("""
                SELECT km FROM car_km
                WHERE car_id = %s ORDER BY recorded_at DESC, id DESC LIMIT 1
            """, (car_id,))
            km_row = cursor.fetchone()
            current_km = km_row['km'] if km_row else None

            # open alerts with urgency flag
            cursor.execute("""
                SELECT ma.id, ma.part_id, ma.alert_type,
                       ma.due_date, ma.due_km,
                       cp.name AS part_name, cp.category,
                       cp.alert_km_interval,
                       DATEDIFF(ma.due_date, CURDATE()) AS days_left
                FROM maintenance_alerts ma
                JOIN car_parts cp ON ma.part_id = cp.id
                WHERE ma.car_id = %s AND ma.status = 'open'
                ORDER BY ma.due_date ASC
            """, (car_id,))
            raw_alerts = [dict(r) for r in cursor.fetchall()]

            alerts = []
            for a in raw_alerts:
                urgent = False
                due_date = a['due_date']
                due_km = a['due_km']
                days_left = a['days_left']
                km_interval = a['alert_km_interval']

                if due_date and days_left is not None and days_left <= 15:
                    urgent = True
                if due_km and current_km is not None:
                    threshold = int(km_interval * 0.05) if km_interval else 500
                    if current_km >= due_km - threshold:
                        urgent = True
                if not due_date and not due_km:
                    urgent = True

                a['urgent'] = urgent
                a.pop('alert_km_interval', None)
                a.pop('days_left', None)
                alerts.append(a)

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
                'car': dict(car) if car else None,
                'alerts': alerts,
                'parts': parts,
                'garages': garages
            }
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # KM TRACKING                                                          #
    # ------------------------------------------------------------------ #

    def get_current_km(self, car_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT km, recorded_at FROM car_km
                WHERE car_id = %s ORDER BY recorded_at DESC, id DESC LIMIT 1
            """, (car_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            con.close()

    def get_km_history(self, car_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT id, km, recorded_at, notes
                FROM car_km WHERE car_id = %s
                ORDER BY recorded_at DESC, id DESC
            """, (car_id,))
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()

    def log_km(self, car_id, km, recorded_at, notes=None):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                INSERT INTO car_km (car_id, km, recorded_at, notes)
                VALUES (%s, %s, %s, %s)
            """, (car_id, km, recorded_at, notes or None))
            con.commit()
            return cursor.lastrowid
        finally:
            con.close()

    def get_part_intervals(self, part_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT alert_km_interval, alert_month_interval
                FROM car_parts WHERE id = %s
            """, (part_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            con.close()

    def get_all_open_alerts(self):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT ma.id, ma.car_id, ma.part_id, ma.alert_type,
                       ma.due_date, ma.due_km, ma.status, ma.created_at,
                       cp.name AS part_name, cp.category,
                       cp.alert_km_interval,
                       c.plate_number, c.brand,
                       cg.model, cg.year,
                       e.nom, e.prenom,
                       -- days until due (negative = overdue)
                       DATEDIFF(ma.due_date, CURDATE()) AS days_left,
                       -- current km for this car
                       (SELECT km FROM car_km
                        WHERE car_id = ma.car_id
                        ORDER BY recorded_at DESC, id DESC LIMIT 1) AS current_km
                FROM maintenance_alerts ma
                JOIN car_parts cp ON ma.part_id = cp.id
                JOIN cars c ON ma.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                LEFT JOIN car_assignments ca ON ca.car_id = c.id AND ca.end_date IS NULL
                LEFT JOIN employees e ON ca.employee_id = e.id
                WHERE ma.status = 'open'
                ORDER BY ma.due_date ASC, ma.due_km ASC
            """)
            rows = [dict(r) for r in cursor.fetchall()]

            # apply same 15-day / 5% threshold filter as get_alerts_by_car
            import datetime
            today = datetime.date.today()
            result = []
            for alert in rows:
                show = False
                due_date = alert['due_date']
                due_km = alert['due_km']
                current_km = alert['current_km']
                km_interval = alert['alert_km_interval']
                days_left = alert['days_left']

                if due_date:
                    if days_left is not None and days_left <= 15:
                        show = True

                if due_km and current_km is not None:
                    threshold = int(km_interval * 0.05) if km_interval else 500
                    if current_km >= due_km - threshold:
                        show = True

                if not due_date and not due_km:
                    show = True

                if show:
                    result.append(alert)

            return result
        finally:
            con.close()