from tools.database_tools import DatabaseTools
import datetime


class DashboardService:
    def __init__(self):
        self.db_tools = DatabaseTools()

    # ------------------------------------------------------------------ #
    # FLEET KPIs                                                           #
    # ------------------------------------------------------------------ #

    def get_fleet_kpis(self):
        """Returns total, active, maintenance, retired, unassigned, incomplete dossier counts."""
        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                SELECT
                    COUNT(*)                                                      AS total,
                    SUM(CASE WHEN c.status = 'active'      THEN 1 ELSE 0 END)    AS active,
                    SUM(CASE WHEN c.status = 'maintenance' THEN 1 ELSE 0 END)    AS maintenance,
                    SUM(CASE WHEN c.status = 'inactive'    THEN 1 ELSE 0 END)    AS inactive,
                    SUM(CASE WHEN c.status = 'retired'     THEN 1 ELSE 0 END)    AS retired,
                    SUM(CASE WHEN ca.car_id IS NULL         THEN 1 ELSE 0 END)    AS unassigned
                FROM cars c
                LEFT JOIN (
                    SELECT DISTINCT car_id FROM car_assignments WHERE end_date IS NULL
                ) ca ON ca.car_id = c.id
            """)
            fleet = cursor.fetchone()

            # incomplete dossiers
            cursor.execute("""
                SELECT COUNT(c.id) AS incomplete
                FROM cars c
                LEFT JOIN (SELECT DISTINCT car_id FROM insurances)       ins ON ins.car_id = c.id
                LEFT JOIN (SELECT DISTINCT car_id FROM vignettes)        vig ON vig.car_id = c.id
                LEFT JOIN (SELECT DISTINCT car_id FROM visite_technique) vt  ON vt.car_id  = c.id
                WHERE ins.car_id IS NULL OR vig.car_id IS NULL OR vt.car_id IS NULL
            """)
            incomplete = cursor.fetchone()['incomplete']

            return {
                'total':       fleet['total']       or 0,
                'active':      fleet['active']       or 0,
                'maintenance': fleet['maintenance']  or 0,
                'inactive':    fleet['inactive']     or 0,
                'retired':     fleet['retired']      or 0,
                'unassigned':  fleet['unassigned']   or 0,
                'incomplete':  incomplete
            }
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # EXPENSE KPIs                                                         #
    # ------------------------------------------------------------------ #

    def get_expense_kpis(self, date_from=None, date_to=None):
        if not date_from:
            date_from = f"{datetime.date.today().year}-01-01"
        if not date_to:
            date_to = datetime.date.today().isoformat()

        con, cursor = self.db_tools.find_connection()
        try:
            # maintenance — sum DISTINCT factures to avoid double counting
            cursor.execute("""
                SELECT COALESCE(SUM(f.montant_ttc), 0) AS total
                FROM factures f
                WHERE f.type = 'maintenance'
                AND f.date_facture BETWEEN %s AND %s
                AND f.montant_ttc IS NOT NULL
            """, (date_from, date_to))
            maintenance = cursor.fetchone()['total']

            # sinistre
            cursor.execute("""
                SELECT COALESCE(SUM(f.montant_ttc), 0) AS total
                FROM factures f
                WHERE f.type = 'sinistre'
                AND f.date_facture BETWEEN %s AND %s
                AND f.montant_ttc IS NOT NULL
            """, (date_from, date_to))
            sinistres = cursor.fetchone()['total']

            # carburant
            cursor.execute("""
                SELECT COALESCE(SUM(montant_ttc), 0) AS total
                FROM carburant_expenses
                WHERE periode BETWEEN %s AND %s
            """, (date_from, date_to))
            carburant = cursor.fetchone()['total']

            # vignettes
            cursor.execute("""
                SELECT COALESCE(SUM(montant), 0) AS total
                FROM vignettes
                WHERE expiration_date BETWEEN %s AND %s
                AND montant IS NOT NULL
            """, (date_from, date_to))
            vignettes = cursor.fetchone()['total']

            # visite technique
            cursor.execute("""
                SELECT COALESCE(SUM(montant), 0) AS total
                FROM visite_technique
                WHERE expiration_date BETWEEN %s AND %s
                AND montant IS NOT NULL
            """, (date_from, date_to))
            visites = cursor.fetchone()['total']

            total = float(maintenance) + float(sinistres) + float(carburant) + float(vignettes) + float(visites)

            return {
                'maintenance': float(maintenance),
                'sinistres': float(sinistres),
                'carburant': float(carburant),
                'vignettes': float(vignettes),
                'visites': float(visites),
                'total': total
            }
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # MONTHLY CHART DATA                                                   #
    # ------------------------------------------------------------------ #

    def get_monthly_expenses(self, date_from=None, date_to=None):
        if not date_from:
            date_from = f"{datetime.date.today().year}-01-01"
        if not date_to:
            date_to = datetime.date.today().isoformat()

        def to_key(row):
            y = str(row['yr'])
            m = str(row['mo']).zfill(2)
            return f"{y}-{m}"

        con, cursor = self.db_tools.find_connection()
        try:
            # maintenance by month
            cursor.execute("""
                SELECT YEAR(date_facture) AS yr, MONTH(date_facture) AS mo,
                       COALESCE(SUM(montant_ttc), 0) AS total
                FROM factures
                WHERE type = 'maintenance'
                AND date_facture BETWEEN %s AND %s
                AND montant_ttc IS NOT NULL
                GROUP BY yr, mo ORDER BY yr, mo
            """, (date_from, date_to))
            maintenance_rows = {to_key(r): float(r['total']) for r in cursor.fetchall()}

            # sinistres by month
            cursor.execute("""
                SELECT YEAR(date_facture) AS yr, MONTH(date_facture) AS mo,
                       COALESCE(SUM(montant_ttc), 0) AS total
                FROM factures
                WHERE type = 'sinistre'
                AND date_facture BETWEEN %s AND %s
                AND montant_ttc IS NOT NULL
                GROUP BY yr, mo ORDER BY yr, mo
            """, (date_from, date_to))
            sinistre_rows = {to_key(r): float(r['total']) for r in cursor.fetchall()}

            # vignettes + visites by month (based on expiration_date)
            cursor.execute("""
                SELECT YEAR(expiration_date) AS yr, MONTH(expiration_date) AS mo,
                       COALESCE(SUM(montant), 0) AS total
                FROM vignettes
                WHERE expiration_date BETWEEN %s AND %s
                AND montant IS NOT NULL
                GROUP BY yr, mo
                UNION ALL
                SELECT YEAR(expiration_date) AS yr, MONTH(expiration_date) AS mo,
                       COALESCE(SUM(montant), 0) AS total
                FROM visite_technique
                WHERE expiration_date BETWEEN %s AND %s
                AND montant IS NOT NULL
                GROUP BY yr, mo
            """, (date_from, date_to, date_from, date_to))
            admin_raw = cursor.fetchall()
            admin_rows = {}
            for r in admin_raw:
                key = to_key(r)
                admin_rows[key] = admin_rows.get(key, 0) + float(r['total'])

            all_months = sorted(set(
                list(maintenance_rows.keys()) +
                list(sinistre_rows.keys()) +
                list(admin_rows.keys())
            ))

            if not all_months:
                return {'labels': [], 'maintenance': [], 'sinistres': [], 'admin': []}

            return {
                'labels': all_months,
                'maintenance': [maintenance_rows.get(m, 0) for m in all_months],
                'sinistres': [sinistre_rows.get(m, 0) for m in all_months],
                'admin': [admin_rows.get(m, 0) for m in all_months],
            }
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # TOP 5 MOST EXPENSIVE CARS                                           #
    # ------------------------------------------------------------------ #

    def get_top_expensive_cars(self, date_from=None, date_to=None):
        if not date_from:
            date_from = f"{datetime.date.today().year}-01-01"
        if not date_to:
            date_to = datetime.date.today().isoformat()

        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                SELECT
                    c.id,
                    c.plate_number,
                    cg.model,
                    COALESCE(f.total_factures, 0)   AS total_factures,
                    COALESCE(cb.total_carburant, 0)  AS total_carburant,
                    COALESCE(f.total_factures, 0) + COALESCE(cb.total_carburant, 0) AS grand_total
                FROM cars c
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                LEFT JOIN (
                    SELECT car_id, SUM(montant_ttc) AS total_factures
                    FROM factures
                    WHERE date_facture BETWEEN %s AND %s
                    AND montant_ttc IS NOT NULL
                    GROUP BY car_id
                ) f ON f.car_id = c.id
                LEFT JOIN (
                    SELECT car_id, SUM(montant_ttc) AS total_carburant
                    FROM carburant_expenses
                    WHERE periode BETWEEN %s AND %s
                    GROUP BY car_id
                ) cb ON cb.car_id = c.id
                ORDER BY grand_total DESC
                LIMIT 5
            """, (date_from, date_to, date_from, date_to))
            return cursor.fetchall()
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # ALERTS                                                               #
    # ------------------------------------------------------------------ #

    def get_alerts(self, days_ahead=30):
        """
        Returns all active alerts:
        - Documents expiring within days_ahead days
        - Incomplete dossiers
        """
        today    = datetime.date.today()
        deadline = (today + datetime.timedelta(days=days_ahead)).isoformat()
        today_str = today.isoformat()

        con, cursor = self.db_tools.find_connection()
        alerts = []

        try:
            # expiring assurances
            cursor.execute("""
                SELECT c.id AS car_id, c.plate_number, cg.model,
                       i.end_date AS expiry, 'assurance' AS doc_type
                FROM insurances i
                JOIN cars c ON i.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE i.end_date BETWEEN %s AND %s
                AND i.status != 'cancelled'
            """, (today_str, deadline))
            for r in cursor.fetchall():
                days = (datetime.date.fromisoformat(str(r['expiry'])) - today).days
                alerts.append({
                    'type':    'expiry',
                    'doc':     'Assurance',
                    'car_id':  r['car_id'],
                    'car':     f"{r['model'] or ''} — {r['plate_number'] or ''}",
                    'expiry':  str(r['expiry']),
                    'days':    days,
                    'level':   'danger' if days <= 7 else 'warning'
                })

            # expiring vignettes
            cursor.execute("""
                SELECT c.id AS car_id, c.plate_number, cg.model,
                       v.expiration_date AS expiry, 'vignette' AS doc_type
                FROM vignettes v
                JOIN cars c ON v.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE v.expiration_date BETWEEN %s AND %s
            """, (today_str, deadline))
            for r in cursor.fetchall():
                days = (datetime.date.fromisoformat(str(r['expiry'])) - today).days
                alerts.append({
                    'type':   'expiry',
                    'doc':    'Vignette',
                    'car_id': r['car_id'],
                    'car':    f"{r['model'] or ''} — {r['plate_number'] or ''}",
                    'expiry': str(r['expiry']),
                    'days':   days,
                    'level':  'danger' if days <= 7 else 'warning'
                })

            # expiring visite technique
            cursor.execute("""
                SELECT c.id AS car_id, c.plate_number, cg.model,
                       vt.expiration_date AS expiry
                FROM visite_technique vt
                JOIN cars c ON vt.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE vt.expiration_date BETWEEN %s AND %s
            """, (today_str, deadline))
            for r in cursor.fetchall():
                days = (datetime.date.fromisoformat(str(r['expiry'])) - today).days
                alerts.append({
                    'type':   'expiry',
                    'doc':    'Visite Technique',
                    'car_id': r['car_id'],
                    'car':    f"{r['model'] or ''} — {r['plate_number'] or ''}",
                    'expiry': str(r['expiry']),
                    'days':   days,
                    'level':  'danger' if days <= 7 else 'warning'
                })

            # already expired documents
            cursor.execute("""
                SELECT c.id AS car_id, c.plate_number, cg.model,
                       i.end_date AS expiry, 'assurance' AS doc_type
                FROM insurances i
                JOIN cars c ON i.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE i.end_date < %s AND i.status != 'cancelled'
            """, (today_str,))
            for r in cursor.fetchall():
                alerts.append({
                    'type':   'expired',
                    'doc':    'Assurance',
                    'car_id': r['car_id'],
                    'car':    f"{r['model'] or ''} — {r['plate_number'] or ''}",
                    'expiry': str(r['expiry']),
                    'days':   0,
                    'level':  'danger'
                })

            # incomplete dossiers
            cursor.execute("""
                SELECT c.id AS car_id, c.plate_number, cg.model,
                    CASE WHEN ins.car_id IS NULL THEN 1 ELSE 0 END AS missing_assurance,
                    CASE WHEN vig.car_id IS NULL THEN 1 ELSE 0 END AS missing_vignette,
                    CASE WHEN vt.car_id  IS NULL THEN 1 ELSE 0 END AS missing_visite
                FROM cars c
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                LEFT JOIN (SELECT DISTINCT car_id FROM insurances)       ins ON ins.car_id = c.id
                LEFT JOIN (SELECT DISTINCT car_id FROM vignettes)        vig ON vig.car_id = c.id
                LEFT JOIN (SELECT DISTINCT car_id FROM visite_technique) vt  ON vt.car_id  = c.id
                WHERE ins.car_id IS NULL OR vig.car_id IS NULL OR vt.car_id IS NULL
            """)
            for r in cursor.fetchall():
                missing = []
                if r['missing_assurance']: missing.append('Assurance')
                if r['missing_vignette']:  missing.append('Vignette')
                if r['missing_visite']:    missing.append('Visite Technique')
                alerts.append({
                    'type':    'incomplete',
                    'doc':     ', '.join(missing),
                    'car_id':  r['car_id'],
                    'car':     f"{r['model'] or ''} — {r['plate_number'] or ''}",
                    'expiry':  None,
                    'days':    None,
                    'level':   'warning'
                })

            # sort: danger first, then by days
            alerts.sort(key=lambda a: (0 if a['level'] == 'danger' else 1, a['days'] or 999))
            return alerts

        finally:
            con.close()

    def get_all_alerts_combined(self, days_ahead=30):
        """Combines document alerts + maintenance alerts for the bell"""
        alerts = self.get_alerts(days_ahead)

        # add maintenance alerts
        from services.maintenance import MaintenanceService
        maintenance_service = MaintenanceService()
        maintenance_alerts = maintenance_service.get_all_open_alerts()

        for a in maintenance_alerts:
            alerts.append({
                'type': 'maintenance',
                'doc': a['part_name'],
                'car_id': a['car_id'],
                'car': f"{a['model'] or ''} — {a['plate_number'] or ''}",
                'expiry': str(a['due_date']) if a['due_date'] else None,
                'days': a['days_left'],
                'level': 'danger' if (a['days_left'] is not None and a['days_left'] <= 0) else 'warning'
            })

        # re-sort
        alerts.sort(key=lambda a: (0 if a['level'] == 'danger' else 1, a['days'] or 999))
        return alerts

    def get_fleet_risk_score(self):
        """Calculate fleet health risk score 0-100 (100 = perfect health)"""
        con, cursor = self.db_tools.find_connection()
        try:
            issues = []
            penalties = 0

            # 1. Expired documents (25 points max)
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM insurances
                WHERE end_date < CURDATE() AND status != 'cancelled'
            """)
            expired_insurance = cursor.fetchone()['cnt']

            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM vignettes
                WHERE expiration_date < CURDATE()
            """)
            expired_vignettes = cursor.fetchone()['cnt']

            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM visite_technique
                WHERE expiration_date < CURDATE()
            """)
            expired_visites = cursor.fetchone()['cnt']

            expired_docs = expired_insurance + expired_vignettes + expired_visites
            doc_penalty = min(25, expired_docs * 5)
            penalties += doc_penalty
            if expired_docs > 0:
                issues.append({
                    'icon': 'fa-file-times',
                    'color': 'danger',
                    'text': f"{expired_docs} document(s) expiré(s)",
                    'link': '/dashboard/cars'
                })

            # 2. Open sinistres (20 points max)
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM sinistres
                WHERE status IN ('ouvert', 'en_cours')
            """)
            open_sinistres = cursor.fetchone()['cnt']
            sin_penalty = min(20, open_sinistres * 5)
            penalties += sin_penalty
            if open_sinistres > 0:
                issues.append({
                    'icon': 'fa-car-crash',
                    'color': 'danger',
                    'text': f"{open_sinistres} sinistre(s) ouvert(s)",
                    'link': '/dashboard/cars'
                })

            # 3. Overdue maintenance alerts (25 points max)
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM maintenance_alerts
                WHERE status = 'open'
                AND (
                    (due_date IS NOT NULL AND due_date < CURDATE())
                    OR
                    (due_km IS NOT NULL AND due_km < (
                        SELECT COALESCE(MAX(km), 0) FROM car_km
                        WHERE car_id = maintenance_alerts.car_id
                    ))
                )
            """)
            overdue_maintenance = cursor.fetchone()['cnt']
            maint_penalty = min(25, overdue_maintenance * 5)
            penalties += maint_penalty
            if overdue_maintenance > 0:
                issues.append({
                    'icon': 'fa-tools',
                    'color': 'warning',
                    'text': f"{overdue_maintenance} alerte(s) maintenance en retard",
                    'link': '/dashboard/maintenance-alerts'
                })

            # 4. Unassigned active cars (15 points max)
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM cars c
                WHERE c.status = 'active'
                AND NOT EXISTS (
                    SELECT 1 FROM car_assignments ca
                    WHERE ca.car_id = c.id AND ca.end_date IS NULL
                )
            """)
            unassigned = cursor.fetchone()['cnt']
            unassigned_penalty = min(15, unassigned * 3)
            penalties += unassigned_penalty
            if unassigned > 0:
                issues.append({
                    'icon': 'fa-user-slash',
                    'color': 'warning',
                    'text': f"{unassigned} véhicule(s) actif(s) non affecté(s)",
                    'link': '/dashboard/cars'
                })

            # 5. Incomplete dossiers (15 points max)
            cursor.execute("""
                SELECT COUNT(*) AS cnt FROM cars c
                WHERE c.status != 'retired'
                AND (
                    NOT EXISTS (SELECT 1 FROM insurances WHERE car_id = c.id)
                    OR NOT EXISTS (SELECT 1 FROM vignettes WHERE car_id = c.id)
                    OR NOT EXISTS (SELECT 1 FROM visite_technique WHERE car_id = c.id)
                )
            """)
            incomplete = cursor.fetchone()['cnt']
            incomplete_penalty = min(15, incomplete * 3)
            penalties += incomplete_penalty
            if incomplete > 0:
                issues.append({
                    'icon': 'fa-folder-open',
                    'color': 'warning',
                    'text': f"{incomplete} dossier(s) incomplet(s)",
                    'link': '/dashboard/cars'
                })

            score = max(0, 100 - penalties)

            if score >= 81:
                level = 'success'
                label = 'Bon'
            elif score >= 61:
                level = 'warning'
                label = 'Acceptable'
            elif score >= 31:
                level = 'orange'
                label = 'Attention'
            else:
                level = 'danger'
                label = 'Critique'

            return {
                'score': score,
                'level': level,
                'label': label,
                'issues': issues
            }
        finally:
            con.close()

    def get_all_cars_expenses(self, date_from=None, date_to=None):
        if not date_from:
            date_from = f"{datetime.date.today().year}-01-01"
        if not date_to:
            date_to = datetime.date.today().isoformat()

        con, cursor = self.db_tools.find_connection()
        try:
            cursor.execute("""
                SELECT
                    c.id,
                    c.plate_number,
                    c.brand,
                    cg.model,
                    cg.year,
                    c.status,
                    COALESCE(f.total_factures, 0)  AS total_maintenance,
                    COALESCE(s.total_sinistres, 0)  AS total_sinistres,
                    COALESCE(cb.total_carburant, 0) AS total_carburant,
                    COALESCE(f.total_factures, 0) +
                    COALESCE(s.total_sinistres, 0) +
                    COALESCE(cb.total_carburant, 0) AS grand_total,
                    (SELECT km FROM car_km
                     WHERE car_id = c.id
                     ORDER BY recorded_at DESC, id DESC LIMIT 1) AS current_km,
                    (SELECT CONCAT(e.prenom, ' ', e.nom)
                     FROM car_assignments ca
                     JOIN employees e ON ca.employee_id = e.id
                     WHERE ca.car_id = c.id AND ca.end_date IS NULL
                     LIMIT 1) AS assigned_to
                FROM cars c
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                LEFT JOIN (
                    SELECT car_id, SUM(montant_ttc) AS total_factures
                    FROM factures
                    WHERE type = 'maintenance'
                    AND date_facture BETWEEN %s AND %s
                    AND montant_ttc IS NOT NULL
                    GROUP BY car_id
                ) f ON f.car_id = c.id
                LEFT JOIN (
                    SELECT car_id, SUM(montant_ttc) AS total_sinistres
                    FROM factures
                    WHERE type = 'sinistre'
                    AND date_facture BETWEEN %s AND %s
                    AND montant_ttc IS NOT NULL
                    GROUP BY car_id
                ) s ON s.car_id = c.id
                LEFT JOIN (
                    SELECT car_id, SUM(montant_ttc) AS total_carburant
                    FROM carburant_expenses
                    WHERE periode BETWEEN %s AND %s
                    GROUP BY car_id
                ) cb ON cb.car_id = c.id
                ORDER BY grand_total DESC
            """, (date_from, date_to, date_from, date_to, date_from, date_to))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                for k in ['total_maintenance', 'total_sinistres', 'total_carburant', 'grand_total']:
                    d[k] = float(d[k]) if d[k] else 0.0
                result.append(d)
            return result
        finally:
            con.close()