from flask import Flask, redirect, url_for, render_template

from blueprints.auth import auth_bp

app = Flask(__name__)
app.secret_key = 'sex'

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
@app.route('/employer')
def employer():
    return render_template('employer.html')
@app.route('/detaille')
def detaille ():
    return render_template('detaille.html')

app.register_blueprint(auth_bp, url_prefix='/auth')
if __name__ == '__main__':
    app.run()