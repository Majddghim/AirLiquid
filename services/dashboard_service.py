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
        """
        Returns total expenses by category for the given period.
        If no dates provided, defaults to current year.
        """
        if not date_from:
            date_from = f"{datetime.date.today().year}-01-01"
        if not date_to:
            date_to = datetime.date.today().isoformat()

        con, cursor = self.db_tools.find_connection()
        try:
            # maintenance factures
            cursor.execute("""
                SELECT COALESCE(SUM(montant_ttc), 0) AS total
                FROM factures
                WHERE type = 'maintenance'
                AND date_facture BETWEEN %s AND %s
                AND extraction_status = 'verified'
            """, (date_from, date_to))
            maintenance = cursor.fetchone()['total']

            # sinistre factures
            cursor.execute("""
                SELECT COALESCE(SUM(montant_ttc), 0) AS total
                FROM factures
                WHERE type = 'sinistre'
                AND date_facture BETWEEN %s AND %s
                AND extraction_status = 'verified'
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
                'sinistres':   float(sinistres),
                'carburant':   float(carburant),
                'vignettes':   float(vignettes),
                'visites':     float(visites),
                'total':       total
            }
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # MONTHLY CHART DATA                                                   #
    # ------------------------------------------------------------------ #

    def get_monthly_expenses(self, date_from=None, date_to=None):
        """
        Returns monthly expense breakdown by category for chart rendering.
        Uses YEAR/MONTH instead of DATE_FORMAT to avoid pymysql bytes issue.
        """
        if not date_from:
            date_from = f"{datetime.date.today().year}-01-01"
        if not date_to:
            date_to = datetime.date.today().isoformat()

        def to_key(row):
            """Convert YEAR + MONTH columns to 'YYYY-MM' string safely."""
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
                AND extraction_status = 'verified'
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
                AND extraction_status = 'verified'
                GROUP BY yr, mo ORDER BY yr, mo
            """, (date_from, date_to))
            sinistre_rows = {to_key(r): float(r['total']) for r in cursor.fetchall()}

            # carburant by month
            cursor.execute("""
                SELECT YEAR(periode) AS yr, MONTH(periode) AS mo,
                       COALESCE(SUM(montant_ttc), 0) AS total
                FROM carburant_expenses
                WHERE periode BETWEEN %s AND %s
                GROUP BY yr, mo ORDER BY yr, mo
            """, (date_from, date_to))
            carburant_rows = {to_key(r): float(r['total']) for r in cursor.fetchall()}

            # build unified month list
            all_months = sorted(set(
                list(maintenance_rows.keys()) +
                list(sinistre_rows.keys()) +
                list(carburant_rows.keys())
            ))

            # if no data at all, return empty structure
            if not all_months:
                return {'labels': [], 'maintenance': [], 'sinistres': [], 'carburant': []}

            return {
                'labels':      all_months,
                'maintenance': [maintenance_rows.get(m, 0) for m in all_months],
                'sinistres':   [sinistre_rows.get(m, 0)    for m in all_months],
                'carburant':   [carburant_rows.get(m, 0)   for m in all_months],
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
                    COALESCE(f.total_factures, 0)  AS total_factures,
                    COALESCE(cb.total_carburant, 0) AS total_carburant,
                    COALESCE(f.total_factures, 0) + COALESCE(cb.total_carburant, 0) AS grand_total
                FROM cars c
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                LEFT JOIN (
                    SELECT car_id, SUM(montant_ttc) AS total_factures
                    FROM factures
                    WHERE date_facture BETWEEN %s AND %s
                    AND extraction_status = 'verified'
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