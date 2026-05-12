from flask import Flask, redirect, url_for, render_template

from blueprints.auth.views import AuthViews
from blueprints.car import car_bp
from blueprints.dashboard import dashboard_bp
from blueprints.employer import employe_bp
from blueprints.guest import guest_bp
from blueprints.settings import settings_bp
from blueprints.maintenance import maintenance_bp
from dotenv import load_dotenv
from blueprints.reports import reports_bp
from apscheduler.schedulers.background import BackgroundScheduler
from services.digest_service import DigestService
from blueprints.gmail import gmail_bp
from blueprints.messages import message_bp

import os
load_dotenv()

import datetime
from flask.json.provider import DefaultJSONProvider
from blueprints.sinistre import sinistre_bp
class CustomJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
app = Flask(__name__)
app.json = CustomJSONProvider(app)
app.secret_key = 'xxx'

def start_scheduler():
    digest_service = DigestService()
    scheduler = BackgroundScheduler()

    # every Monday at 8:00 AM
    scheduler.add_job(
        func=lambda: digest_service.send_digest('majddghim25@gmail.com'),
        trigger='cron',
        day_of_week='mon',
        hour=8,
        minute=0,
        id='weekly_digest'
    )
    scheduler.start()
    print('✅ Scheduler started — weekly digest every Monday at 8:00')

start_scheduler()

# Initialize and register blueprints
auth_views = AuthViews()
app.register_blueprint(auth_views.auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
app.register_blueprint(employe_bp, url_prefix='/employe')
app.register_blueprint(car_bp, url_prefix='/car')
app.register_blueprint(guest_bp, url_prefix='/guest')
app.register_blueprint(settings_bp, url_prefix='/settings')
app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(gmail_bp, url_prefix='/gmail')
app.register_blueprint(message_bp, url_prefix='/messages')


app.register_blueprint(sinistre_bp, url_prefix='/sinistre')
@app.route('/')
def hello_world():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def index():
    return redirect(url_for('dashboard.admin_dashboard'))





if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)