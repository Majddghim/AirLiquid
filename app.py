from flask import Flask, redirect, url_for, render_template

from blueprints.auth.views import AuthViews
from blueprints.dashboard import dashboard_bp

app = Flask(__name__)
app.secret_key = 'xxx'

# Initialize and register blueprints
auth_views = AuthViews()
app.register_blueprint(auth_views.auth_bp, url_prefix='/auth')
app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

@app.route('/')
def hello_world():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/dashboard')
def index():
    return render_template('dashboard.html')

@app.route('/profile')
def profile():
    return render_template('profile.html')

@app.route('/employe')
def employer():
    return render_template('employe.html')

@app.route('/ajout-voiture')
def voiture():
    return render_template('ajout-voiture.html')

@app.route('/ajout-employe')
def detaille():
    return render_template('ajout-employe.html')

if __name__ == '__main__':
    app.run()