"""Minimale Flask Anwendung"""

# Import benötigter Flask-Module
from flask import Flask, render_template, request
from flask_login import login_user, login_required, logout_user, current_user

# Import der Verbindungsinformationen zur Datenbank:
# Variable DB_HOST: Servername des MySQL-Servers
# Variable DB_USER: Nutzername
# Variable DB_PASSWORD: Passwort
# Variable DB_DATABASE: Datenbankname
from db.db_credentials import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE

app = Flask(__name__)


@app.route('/')
def index():
    """Startseite"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')
    return render_template("login.html")


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')


    return render_template("sign_up.html")

@app.route('/logout')
#@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@app.route('/skoch')
def skoch():
    return render_template('skoch.html')


@app.route('/oak')
def oak():
    return render_template('oak.html')


@app.route('/dseljaci')
def dseljaci():
    return render_template('dseljaci.html')


@app.route('/csoenmez')
def csoenmez():
    return render_template('csoenmez.html')


# Start der Flask-Anwendung
if __name__ == '__main__':
    app.run(debug=True)
