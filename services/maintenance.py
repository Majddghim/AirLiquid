from tools.database_tools import DatabaseTools
import datetime
import os
import math
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER


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
    def search_facture_by_num(self, num_facture, car_id):
        """Search for existing facture by number for reuse"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT id, num_facture, date_facture, montant_ttc
                FROM factures
                WHERE num_facture = %s AND car_id = %s
                LIMIT 1
            """, (num_facture, car_id))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            con.close()

    def get_records_by_car(self, car_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT mr.id, mr.car_id, mr.part_id, mr.garage_id,
                       mr.done_at, mr.km_at_service, mr.next_due_date,
                       mr.next_due_km, mr.status, mr.notes, mr.created_at,
                       cp.name AS part_name, cp.category,
                       g.name  AS garage_name,
                       f.id    AS facture_id,
                       f.montant_ttc,
                       f.file_path AS facture_file
                FROM maintenance_records mr
                JOIN car_parts cp ON mr.part_id = cp.id
                LEFT JOIN garages g ON mr.garage_id = g.id
                LEFT JOIN facture_records fr ON fr.record_id = mr.id
                    AND fr.record_type = 'maintenance'
                LEFT JOIN factures f ON f.id = fr.facture_id
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
                SELECT f.id, f.num_facture, f.num_reglement, f.date_facture,
                       f.date_reglement, f.montant_ht, f.montant_ttc,
                       f.tva, f.file_path
                FROM factures f
                JOIN facture_records fr ON fr.facture_id = f.id
                WHERE fr.record_id = %s AND fr.record_type = 'maintenance'
                LIMIT 1
            """, (record_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            con.close()

    def attach_facture(self, record_id, car_id, num_facture, num_reglement,
                       date_facture, date_reglement, montant_ht, montant_ttc,
                       tva, file_path=None, existing_facture_id=None):
        con, cursor = self.db.find_connection()
        try:
            con.autocommit(False)

            if existing_facture_id:
                # reuse existing facture — just create the link
                facture_id = existing_facture_id
            else:
                # create new facture
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
                facture_id = cursor.lastrowid

            # create junction record
            cursor.execute("""
                INSERT INTO facture_records (facture_id, record_id, record_type)
                VALUES (%s, %s, 'maintenance')
            """, (facture_id, record_id))

            con.commit()
            return facture_id
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
            # check if this is the first KM entry for this car
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM car_km WHERE car_id = %s
            """, (car_id,))
            is_first = cursor.fetchone()['cnt'] == 0

            cursor.execute("""
                INSERT INTO car_km (car_id, km, recorded_at, notes)
                VALUES (%s, %s, %s, %s)
            """, (car_id, km, recorded_at, notes or None))
            con.commit()
            new_id = cursor.lastrowid

            # if first KM ever, auto-create maintenance alerts
            if is_first:
                self.initialize_alerts_for_car(car_id, km)

            return new_id
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

    def initialize_alerts_for_car(self, car_id, current_km):
        """Create initial maintenance alerts for a newly tracked car based on current KM"""
        import math
        con, cursor = self.db.find_connection()
        try:
            # check if alerts already exist for this car
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM maintenance_alerts
                WHERE car_id = %s
            """, (car_id,))
            if cursor.fetchone()['cnt'] > 0:
                return False  # already initialized

            # get all parts with intervals
            cursor.execute("""
                SELECT id, name, alert_km_interval, alert_month_interval
                FROM car_parts
                WHERE alert_km_interval IS NOT NULL OR alert_month_interval IS NOT NULL
            """)
            parts = cursor.fetchall()

            today = datetime.date.today()
            created = 0

            for part in parts:
                next_km = None
                next_date = None
                alert_type = None

                # calculate next KM threshold
                if part['alert_km_interval']:
                    interval = part['alert_km_interval']
                    # next multiple strictly greater than current
                    next_km = (math.floor(current_km / interval) + 1) * interval
                    alert_type = 'km'

                # calculate next date (today + interval months)
                if part['alert_month_interval']:
                    months = part['alert_month_interval']
                    next_date = today.replace(year=today.year + (today.month + months - 1) // 12,
                                              month=((today.month + months - 1) % 12) + 1)
                    alert_type = 'both' if next_km else 'date'

                if next_km or next_date:
                    cursor.execute("""
                        INSERT INTO maintenance_alerts
                            (car_id, part_id, alert_type, due_date, due_km, status)
                        VALUES (%s, %s, %s, %s, %s, 'open')
                    """, (car_id, part['id'], alert_type, next_date, next_km))
                    created += 1

            con.commit()
            return created
        finally:
            con.close()

    def get_odometer_photos(self, car_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT km, recorded_at, notes, file_path
                FROM car_km
                WHERE car_id = %s AND file_path IS NOT NULL
                ORDER BY recorded_at DESC, id DESC
            """, (car_id,))
            return [dict(r) for r in cursor.fetchall()]
        finally:
            con.close()

    def get_assigned_employee(self, car_id):
        """Get currently assigned employee for a car"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT e.email, e.prenom, e.nom
                FROM car_assignments ca
                JOIN employees e ON ca.employee_id = e.id
                WHERE ca.car_id = %s AND ca.end_date IS NULL
                LIMIT 1
            """, (car_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
        finally:
            con.close()

    def generate_bon_pdf(self, car, garage, items, date):
        """Generate BDC as PDF using ReportLab, save to disk, return file path"""

        upload_folder = 'static/uploads/bdc'
        os.makedirs(upload_folder, exist_ok=True)
        filename = f"bdc_{car.get('plate_number', '').replace(' ', '_')}_{datetime.date.today().isoformat()}.pdf"
        file_path = os.path.join(upload_folder, filename)

        BLUE = colors.HexColor('#0d6efd')
        GRAY = colors.HexColor('#6c757d')
        LIGHT = colors.HexColor('#f8f9fc')

        styles = getSampleStyleSheet()
        title_s = ParagraphStyle('T', parent=styles['Title'],
                                 fontSize=18, textColor=BLUE, alignment=TA_CENTER, spaceAfter=2)
        sub_s = ParagraphStyle('S', parent=styles['Normal'],
                               fontSize=9, textColor=GRAY, alignment=TA_CENTER, spaceAfter=4)
        section_s = ParagraphStyle('SEC', parent=styles['Normal'],
                                   fontSize=9, textColor=GRAY, spaceBefore=10, spaceAfter=4,
                                   fontName='Helvetica-Bold')

        doc = SimpleDocTemplate(file_path, pagesize=A4,
                                rightMargin=1.5 * cm, leftMargin=1.5 * cm,
                                topMargin=1.5 * cm, bottomMargin=1.5 * cm)
        elements = []

        elements.append(Paragraph('AIR LIQUIDE TUNISIA', title_s))
        elements.append(Paragraph('Gestion de Flotte', sub_s))
        elements.append(HRFlowable(width='100%', thickness=3, color=BLUE))
        elements.append(Spacer(1, 0.3 * cm))
        elements.append(Paragraph('BON DE COMMANDE', ParagraphStyle('BDC',
                                                                    parent=styles['Heading1'], fontSize=14,
                                                                    textColor=colors.HexColor('#2d3748'),
                                                                    alignment=TA_CENTER, spaceAfter=4)))
        elements.append(Paragraph(f'Date: {date}', sub_s))
        elements.append(Spacer(1, 0.3 * cm))

        # car + garage info table
        elements.append(Paragraph('VEHICULE', section_s))
        car_table = Table([
            ['Modèle', f"{car.get('model', '—')} {car.get('brand', '')}",
             'Immatriculation', car.get('plate_number', '—')],
            ['Année', str(car.get('year', '—')),
             'Propriétaire', car.get('owner_name', '—')],
        ], colWidths=[3 * cm, 6 * cm, 3 * cm, 6 * cm])
        car_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT),
            ('BACKGROUND', (2, 0), (2, -1), LIGHT),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('ROWHEIGHT', (0, 0), (-1, -1), 18),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(car_table)
        elements.append(Spacer(1, 0.3 * cm))

        elements.append(Paragraph('GARAGE', section_s))
        garage_table = Table([
            ['Nom', garage.get('name', '—'),
             'Téléphone', garage.get('phone', '—')],
            ['Adresse', garage.get('address', '—'),
             'Contact', garage.get('contact_person', '—')],
        ], colWidths=[3 * cm, 6 * cm, 3 * cm, 6 * cm])
        garage_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), LIGHT),
            ('BACKGROUND', (2, 0), (2, -1), LIGHT),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('ROWHEIGHT', (0, 0), (-1, -1), 18),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(garage_table)
        elements.append(Spacer(1, 0.3 * cm))

        # items table
        elements.append(Paragraph('TRAVAUX A EFFECTUER', section_s))
        item_rows = [['#', 'Pièce / Travail', 'Catégorie', 'Remarques']]
        for i, item in enumerate(items):
            item_rows.append([
                str(i + 1),
                item.get('part_name', '—'),
                item.get('category', '—'),
                item.get('notes', ''),
            ])
        items_table = Table(item_rows, colWidths=[1 * cm, 6 * cm, 4 * cm, 7 * cm])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), BLUE),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dee2e6')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, LIGHT]),
            ('ROWHEIGHT', (0, 0), (-1, -1), 18),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 1 * cm))

        # signatures
        sig_table = Table(
            [['Signature Responsable Fleet', 'Signature Garage']],
            colWidths=[9 * cm, 9 * cm]
        )
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('TEXTCOLOR', (0, 0), (-1, -1), GRAY),
            ('BOX', (0, 0), (0, 0), 0.5, colors.HexColor('#dee2e6')),
            ('BOX', (1, 0), (1, 0), 0.5, colors.HexColor('#dee2e6')),
            ('ROWHEIGHT', (0, 0), (-1, -1), 60),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        elements.append(sig_table)

        doc.build(elements)
        return file_path