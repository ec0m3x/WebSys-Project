"""Minimale Flask Anwendung"""

# Import benötigter Flask-Module
from flask import Flask, render_template, request, flash
from flask_login import login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
DB_NAME = "database.db"

# Import der Verbindungsinformationen zur Datenbank:
# Variable DB_HOST: Servername des MySQL-Servers
# Variable DB_USER: Nutzername
# Variable DB_PASSWORD: Passwort
# Variable DB_DATABASE: Datenbankname
#from db.db_credentials import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE

app = Flask(__name__)
app.config['SECRET_KEY'] = 'la web de la sys'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
db.init_app(app)

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
    #Eingaben des Benutzers
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        #Eingabe überprüfen
        if len(email) < 4:
            flash('Email muss länger als 4 Zeichen sein!', category='error')
        elif len(first_name) < 2:
            flash('Vorname muss länger als 2 Zeichen sein!', category='error')
        elif len(last_name) < 2:
            flash('Nachname muss länger als 2 Zeichen sein!', category='error')
        elif password1 != password2:
            flash('Passwörter stimmen nicht überein!', category='error')
        elif len(password1) < 7:
            flash('Passwort muss länger als 7 Zeichen sein!', category='error')
        else:
            #Benutzer zur Datenbank hinzufügen
            flash('Account erfolgreich erstellt', category='success')

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

@app.route('/about_us')
def about_us():
    return render_template('about_us.html')

# Start der Flask-Anwendung
if __name__ == '__main__':
    app.run(debug=True)
