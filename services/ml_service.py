import numpy as np
import datetime
from tools.database_tools import DatabaseTools
from sklearn.linear_model import LinearRegression


class MLService:
    def __init__(self):
        self.db = DatabaseTools()

    # ------------------------------------------------------------------ #
    # PREDICT KM PER DAY FOR A CAR                                        #
    # ------------------------------------------------------------------ #

    def get_km_rate(self, car_id):
        """Calculate average KM per day based on history"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT km, recorded_at FROM car_km
                WHERE car_id = %s
                ORDER BY recorded_at ASC
            """, (car_id,))
            rows = cursor.fetchall()
            if len(rows) < 2:
                return None

            # use first and last entry
            first = rows[0]
            last  = rows[-1]

            km_diff   = last['km'] - first['km']
            day_diff  = (last['recorded_at'] - first['recorded_at']).days

            if day_diff <= 0 or km_diff <= 0:
                return None

            return round(km_diff / day_diff, 1)
        finally:
            con.close()

    def get_current_km(self, car_id):
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT km, recorded_at FROM car_km
                WHERE car_id = %s
                ORDER BY recorded_at DESC, id DESC
                LIMIT 1
            """, (car_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # PREDICT MAINTENANCE DATES                                            #
    # ------------------------------------------------------------------ #

    def predict_maintenance(self, car_id):
        """Predict when each open alert will trigger based on KM rate"""
        con, cursor = self.db.find_connection()
        try:
            km_rate   = self.get_km_rate(car_id)
            current   = self.get_current_km(car_id)
            today     = datetime.date.today()
            predictions = []

            # get open alerts for this car
            cursor.execute("""
                SELECT ma.id, ma.alert_type, ma.due_date, ma.due_km,
                       cp.name AS part_name, cp.category
                FROM maintenance_alerts ma
                JOIN car_parts cp ON ma.part_id = cp.id
                WHERE ma.car_id = %s AND ma.status = 'open'
                ORDER BY ma.due_date ASC
            """, (car_id,))
            alerts = [dict(r) for r in cursor.fetchall()]

            for alert in alerts:
                pred = {
                    'part_name':      alert['part_name'],
                    'category':       alert['category'],
                    'alert_type':     alert['alert_type'],
                    'due_date':       str(alert['due_date']) if alert['due_date'] else None,
                    'due_km':         alert['due_km'],
                    'predicted_date': None,
                    'days_until':     None,
                    'confidence':     'low'
                }

                # predict by KM
                if alert['due_km'] and km_rate and current:
                    current_km   = current['km']
                    km_remaining = alert['due_km'] - current_km
                    if km_remaining > 0 and km_rate > 0:
                        days_until          = round(km_remaining / km_rate)
                        predicted_date      = today + datetime.timedelta(days=days_until)
                        pred['predicted_date'] = str(predicted_date)
                        pred['days_until']     = days_until
                        pred['confidence']     = 'high' if len([r for r in alerts]) >= 3 else 'medium'
                    elif km_remaining <= 0:
                        pred['predicted_date'] = str(today)
                        pred['days_until']     = 0
                        pred['confidence']     = 'high'

                # fallback to due_date if no KM prediction
                elif alert['due_date']:
                    due = alert['due_date']
                    days_until          = (due - today).days
                    pred['predicted_date'] = str(due)
                    pred['days_until']     = days_until
                    pred['confidence']     = 'medium'

                predictions.append(pred)

            return {
                'car_id':   car_id,
                'km_rate':  km_rate,
                'current_km': current['km'] if current else None,
                'predictions': predictions
            }
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # PREDICT MONTHLY EXPENSES                                             #
    # ------------------------------------------------------------------ #

    def predict_expenses(self, car_id):
        """Predict next month and next year expenses using scikit-learn LinearRegression"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT YEAR(date_facture) AS yr, MONTH(date_facture) AS mo,
                       SUM(montant_ttc) AS total
                FROM factures
                WHERE car_id = %s
                AND date_facture IS NOT NULL
                AND montant_ttc IS NOT NULL
                GROUP BY yr, mo
                ORDER BY yr, mo
            """, (car_id,))
            rows = cursor.fetchall()

            if len(rows) < 2:
                return None

            totals = [float(r['total']) for r in rows]
            n = len(totals)

            X = np.array(range(n)).reshape(-1, 1)
            y = np.array(totals)

            model = LinearRegression()
            model.fit(X, y)

            slope = model.coef_[0]
            intercept = model.intercept_

            next_month_pred = max(0, model.predict([[n]])[0])
            future_months = np.array(range(n, n + 12)).reshape(-1, 1)
            next_year_pred = max(0, np.sum(model.predict(future_months)))

            avg_monthly = np.mean(totals)

            return {
                'car_id': car_id,
                'avg_monthly': round(avg_monthly, 2),
                'next_month': round(float(next_month_pred), 2),
                'next_year': round(float(next_year_pred), 2),
                'trend': 'up' if slope > 5 else ('down' if slope < -5 else 'stable'),
                'months_analyzed': n,
                'history': [{'month': f"{r['yr']}-{str(r['mo']).zfill(2)}", 'total': float(r['total'])} for r in rows]
            }
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # FLEET-WIDE PREDICTIONS                                               #
    # ------------------------------------------------------------------ #

    def get_fleet_predictions(self):
        """Get predictions for all active cars"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT c.id, c.plate_number, c.brand, cg.model, cg.year
                FROM cars c
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE c.status != 'retired'
                ORDER BY c.id ASC
            """)
            cars = [dict(r) for r in cursor.fetchall()]

            results = []
            for car in cars:
                car_id      = car['id']
                maintenance = self.predict_maintenance(car_id)
                expenses    = self.predict_expenses(car_id)

                results.append({
                    'car':         car,
                    'maintenance': maintenance,
                    'expenses':    expenses
                })

            return results
        finally:
            con.close()

    # ------------------------------------------------------------------ #
    # ANOMALY DETECTION                                                    #
    # ------------------------------------------------------------------ #

    def detect_expense_anomalies(self):
        """Detect cars with abnormally high expenses compared to fleet average"""
        con, cursor = self.db.find_connection()
        try:
            cursor.execute("""
                SELECT f.car_id, c.plate_number, cg.model, c.brand,
                       SUM(f.montant_ttc) AS total,
                       COUNT(f.id) AS nb_factures
                FROM factures f
                JOIN cars c ON f.car_id = c.id
                LEFT JOIN carte_grises cg ON c.current_cg_id = cg.id
                WHERE f.date_facture >= DATE_SUB(CURDATE(), INTERVAL 12 MONTH)
                AND f.montant_ttc IS NOT NULL
                GROUP BY f.car_id, c.plate_number, cg.model, c.brand
            """)
            rows = [dict(r) for r in cursor.fetchall()]

            if len(rows) < 2:
                return []

            totals = np.array([float(r['total']) for r in rows])
            mean   = np.mean(totals)
            std    = np.std(totals)

            anomalies = []
            for i, row in enumerate(rows):
                total     = float(row['total'])
                z_score   = (total - mean) / std if std > 0 else 0
                if z_score > 1.5:  # 1.5 standard deviations above mean
                    anomalies.append({
                        'car_id':       row['car_id'],
                        'plate_number': row['plate_number'],
                        'model':        row['model'],
                        'brand':        row['brand'],
                        'total':        round(total, 2),
                        'fleet_avg':    round(float(mean), 2),
                        'ratio':        round(total / mean, 1),
                        'z_score':      round(z_score, 2)
                    })

            # sort by ratio descending
            anomalies.sort(key=lambda x: x['ratio'], reverse=True)
            return anomalies
        finally:
            con.close()