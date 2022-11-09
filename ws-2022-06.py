# Import benötigter Flask-Module
from flask import Flask, render_template, request, flash, session, url_for, g, redirect
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector

# db = SQLAlchemy()
# DB_NAME = "database.db"

# Import der Verbindungsinformationen zur Datenbank:
# Variable DB_HOST: Servername des MySQL-Servers
# Variable DB_USER: Nutzername
# Variable DB_PASSWORD: Passwort
# Variable DB_DATABASE: Datenbankname
from db.db_credentials import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE

app = Flask(__name__)
app.secret_key = 'la web de la sys'


# app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
# db.init_app(app)
@app.before_request
def before_request():
    """ Verbindung zur Datenbank herstellen """
    g.con = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD,
                                    database=DB_DATABASE)


@app.teardown_request
def teardown_request(exception):  # pylint: disable=unused-argument
    """ Verbindung zur Datenbank trennen """
    con = getattr(g, 'con', None)
    if con is not None:
        con.close()


@app.route('/')
def index():
    """Startseite"""
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    return render_template("login.html")


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        # Prüfen auf bereits bestehende Einträge
        cursor = g.con.cursor()
        cursor.execute('SELECT email FROM users where email= %s', (request.form.get('email'),))
        row = cursor.fetchone()
        cursor.close()
        if row is not None:
            flash("Email ist bereits vergeben", category="error")
            return redirect(url_for('index'))


"""
        cursor = g.con.cursor()
        cursor.execute('SELECT email FROM users where email= %s', (request.form.get('email'),))
        row = cursor.fetchone()
        cursor.close()
        if row is not None:
            flash("Email ist bereits vergeben", category="error")
            return redirect(url_for('index'))
"""
# Eingaben des Benutzers in Variablen speichern
"""
        username = request.form.get('username')
        first_name = request.form.get('firstName')
        last_name = request.form.get('lastName')
        email = request.form.get('email')
        street = request.form.get('strasse')
        plz = request.form.get('plz')
        city = request.form.get('stadt')
        telephone = request.form.get('tel')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
"""

"""
    # Eingabe überprüfen
        if len(email) < 4:
            flash('Email muss länger als 4 Zeichen sein!', category='error')
            return redirect(url_for('index'))
        elif len(username) < 2:
            flash('Benutzername muss länger als 2 Zeichen sein', category='error')
            return redirect(url_for('index'))
        elif len(first_name) < 2:
            flash('Vorname muss länger als 2 Zeichen sein!', category='error')
            return redirect(url_for('index'))
        elif len(last_name) < 2:
            flash('Nachname muss länger als 2 Zeichen sein!', category='error')
            return redirect(url_for('index'))
        elif password1 != password2:
            flash('Passwörter stimmen nicht überein!', category='error')
            return redirect(url_for('index'))
        elif len(password1) < 7:
            flash('Passwort muss länger als 7 Zeichen sein!', category='error')
            return redirect(url_for('index'))
        else:
"""  # Benutzer zur Datenbank hinzufügen
        if request.form['password1'] == request.form['password2']:
            password = generate_password_hash(password1)

# Nutzer in der Datenbank anlegen
            cursor = g.con.cursor()
            cursor.execute('INSERT INTO users (email, password) VALUES (%s, %s)', (request.form['email'], password,))
            g.con.commit()
            cursor.close()

            flash('Account erfolgreich erstellt', category='success')
            return redirect(url_for('index'))
        return render_template("sign_up.html")


@app.route('/logout')
# @login_required
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
