# Import benötigter Flask-Module
from functools import wraps
from flask import Flask, render_template, request, flash, session, url_for, g, redirect
from werkzeug.security import check_password_hash, generate_password_hash
import mysql.connector

# Import der Verbindungsinformationen zur Datenbank:
# Variable DB_HOST: Servername des MySQL-Servers
# Variable DB_USER: Nutzername
# Variable DB_PASSWORD: Passwort
# Variable DB_DATABASE: Datenbankname
from db.db_credentials import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE

app = Flask(__name__)
app.secret_key = 'la web de la sys'


def login_required(logged_in):
    """ Definiere View Decorator login_required """

    @wraps(logged_in)
    def check_login(*args, **kwargs):
        """ Überprüft, ob Nutzer eingeloggt ist """
        if session.get("username"):
            # Nutzername ist in Session, Nutzer ist eingeloggt
            return logged_in(*args, **kwargs)

        # Weiterleitung zur Login Seite
        flash("Bitte einloggen!", category="error")
        return redirect(url_for("login"))

    return check_login


@app.before_request
def before_request():
    """ Verbindung zur Datenbank herstellen """
    g.con = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_DATABASE)


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


@app.route('/admin')
# Admin Bereich
@login_required
def admin():
    # Alle Nutzer als dictionaries auslesen
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, name, email FROM users', )
    nutzerdaten = cursor.fetchall()
    # print(nutzerdaten)
    cursor.close()
    return render_template('admin.html', nutzerdaten=nutzerdaten)


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    """Hauptseite"""

    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, name, email FROM users where name = %s', (session.get("username"),))
    nutzerdaten = cursor.fetchall()
    cursor.close()
    return render_template('home.html', nutzerdaten=nutzerdaten)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Login """

    if request.method == 'POST':
        cursor = g.con.cursor()
        cursor.execute('SELECT password FROM users where name = %s', (request.form["username"],))
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            flash("Nutzername existiert nicht!", category="error")
            return redirect(url_for('login'))

        pw_from_db = row[0]
        if check_password_hash(pwhash=pw_from_db, password=request.form["password"]):
            # Speichern des Usernamens in der Session
            session['username'] = request.form['username']
            flash("Eingeloggt!")
            return redirect(url_for('home'))

        flash("Passwort nicht korrekt!", category="error")
    return render_template("login.html")


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        cursor = g.con.cursor(buffered=True)
        cursor.execute('SELECT name, email FROM users where name = %s', (request.form["username"],))
        row = cursor.fetchone()
        # print(row)
        cursor.close()
        # Prüfen ob Datenbank schon einen Eintrag hat mit dem Benutzer oder Email hat
        if row is not None:
            flash("Benutzername ist bereits vergeben", category="error")
            return redirect(url_for('sign_up'))

        cursor = g.con.cursor(buffered=True)
        cursor.execute('SELECT email FROM users where email = %s', (request.form["email"],))
        row = cursor.fetchone()
        # print(row)
        cursor.close()

        if row is not None:
            flash("Email ist bereits vergeben", category="error")
            return redirect(url_for('sign_up'))
        # Prüfen ob Passwörter übereinstimmen
        if request.form['password1'] == request.form['password2']:
            password = generate_password_hash(password=request.form['password1'])

            cursor = g.con.cursor()
            cursor.execute('INSERT INTO users (name, email, password) VALUES (%s, %s, %s)',
                           (request.form['username'], request.form['email'], password,))
            g.con.commit()
            cursor.close()
            flash("Benutzer angelegt!")
            return redirect(url_for('index'))

    return render_template("sign_up.html")


@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    flash("Erfolgreich ausgeloggt!")
    return redirect(url_for('index'))


@app.route('/about_us')
def about_us():
    return render_template('about_us.html')


@app.route('/createtable', methods=['GET', 'POST'])
@login_required
def createtable():
    if request.method == 'POST':
        cursor = g.con.cursor()
        cursor.execute('INSERT INTO `table` (capacity, date, time) VALUES (%s, %s, %s)',
                       (request.form['capacity'], request.form['date'], request.form['time']))
        g.con.commit()
        cursor.close()
        flash('Tisch angelegt.')
    return render_template('createtable.html')

@app.route('/deletetable', methods=['GET', 'POST'])
@login_required
def deletetable():
    if request.method == 'POST':
        cursor = g.con.cursor()
        cursor.execute('SELECT capacity FROM `table` where capacity = %s', (request.form["capacity"],))
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            flash("Tisch existiert nicht!", category="error")
            return redirect(url_for('deletetable'))

        cursor = g.con.cursor()
        cursor.execute("DELETE FROM `table` WHERE capacity=%s", (request.form['capacity'],))
        g.con.commit()
        cursor.close()
    return render_template('deletetable.html')


@app.route('/userdata/<int:user_id>', methods=['GET', 'POST'])
@login_required
def userdata(user_id):
    cursor = g.con.cursor(dictionary=True)
    if request.method == "POST":
        cursor.execute("UPDATE `users` SET name=%s, email=%s WHERE id=%s",
                       (request.form['name'], request.form['email'],
                        user_id,))
        g.con.commit()
    cursor.execute("SELECT id, name, email FROM `users` WHERE id=%s", (user_id,))
    daten = cursor.fetchone()
    cursor.close()
    return render_template('userdata.html', htmldaten=daten)

# Start der Flask-Anwendung
if __name__ == '__main__':
    app.run(debug=True)
