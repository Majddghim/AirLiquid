from tools.email_tools import send_weekly_digest
from services.dashboard_service import DashboardService
from services.ml_service import MLService
import datetime


class DigestService:
    def __init__(self):
        self.dashboard = DashboardService()
        self.ml        = MLService()

    def send_digest(self, to_email):
        """Collect all data and send weekly digest email"""
        try:
            today    = datetime.date.today()
            date_from = today.replace(day=1).isoformat()
            date_to   = today.isoformat()

            fleet    = self.dashboard.get_fleet_kpis()
            expenses = self.dashboard.get_expense_kpis(date_from, date_to)
            alerts   = self.dashboard.get_all_alerts_combined(days_ahead=30)
            anomalies = self.ml.detect_expense_anomalies()

            data = {
                'fleet':     fleet,
                'expenses':  expenses,
                'alerts':    alerts,
                'anomalies': anomalies
            }

            result = send_weekly_digest(to_email, data)
            print(f'Weekly digest sent to {to_email}: {result}')
            return result

        except Exception as e:
            print(f'Digest error: {e}')
            return False