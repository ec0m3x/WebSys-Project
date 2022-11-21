# Import benötigter Flask-Module
from functools import wraps
from flask import Flask, render_template, request, flash, session, url_for, g, redirect
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
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
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, starttime, endtime, tableid, userid FROM reservations', )
    reservierungdaten = cursor.fetchall()
    cursor.close()

    # Alle Nutzer als dictionaries auslesen
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, name, email FROM users', )
    nutzerdaten = cursor.fetchall()
    # print(nutzerdaten)
    cursor.close()

    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, capacity FROM `table`', )
    tischdaten = cursor.fetchall()
    cursor.close()
    return render_template('admin.html', reservierungdaten=reservierungdaten, nutzerdaten=nutzerdaten,
                           tischdaten=tischdaten)


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    """Hauptseite"""

    cursor = g.con.cursor()
    cursor.execute('SELECT id FROM users where name = %s', (session.get("username"),))
    row = cursor.fetchone()
    user_id = row[0]
    cursor.close()

    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, starttime, endtime, tableid FROM `reservations` where userid = %s', (user_id,))
    reservierungdaten = cursor.fetchall()
    cursor.close()

    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, name, email FROM users where name = %s', (session.get("username"),))
    nutzerdaten = cursor.fetchall()
    cursor.close()

    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT capacity FROM `table`', )
    tischdaten = cursor.fetchall()
    cursor.close()

    if request.method == "POST":

        cursor = g.con.cursor(buffered=True)
        cursor.execute('SELECT id FROM `table` where capacity >= %s', (request.form["capacity"],))
        row2 = cursor.fetchone()
        cursor.close()
        if row2 is None:
            flash("Kein Tisch für diese Personenanzahl gefunden!", category="error")
            return redirect(url_for('home'))
        table_id = row2[0]

        '''2 Stunden Dauer nicht überschreiten'''
        starttime = datetime.strptime(request.form["starttime"], '%Y-%m-%dT%H:%M')
        endtime= datetime.strptime(request.form["endtime"], '%Y-%m-%dT%H:%M')
        diff = endtime - starttime
        sec = diff.total_seconds()
        hours = sec / (60 * 60)

        if hours > 2:
            flash("Dauer der Reservierung darf 2 Stunden nicht überschreiten!", category="error")
            return redirect(url_for('home'))

        cursor = g.con.cursor(buffered=True)
        cursor.execute('SELECT starttime, endtime FROM `reservations` where %s between starttime and endtime',
                       (request.form["starttime"],))
        row3 = cursor.fetchone()
        cursor.close()

        cursor = g.con.cursor(buffered=True)
        cursor.execute('SELECT starttime, endtime FROM `reservations` where %s between starttime and endtime',
                       (request.form["endtime"],))
        row4 = cursor.fetchone()
        cursor.close()

        cursor = g.con.cursor(buffered=True)
        cursor.execute('SELECT tableid FROM `reservations` where %s between starttime and endtime',
                       (request.form["starttime"],))
        row5 = cursor.fetchone()
        cursor.close()

        cursor = g.con.cursor(buffered=True)
        cursor.execute('SELECT tableid FROM `reservations` where %s between starttime and endtime',
                       (request.form["endtime"],))
        row6 = cursor.fetchone()
        cursor.close()

        if (row3 is not None or row4 is not None) and \
                (row5 is not None and table_id == row5[0] or row6 is not None and table_id == row6[0]):
            flash("Kein Tisch mit dieser Kapazität ist zur ausgewählten Uhrzeit verfügbar.", category="error")
            return redirect(url_for('home'))

        cursor = g.con.cursor()
        cursor.execute('INSERT INTO `reservations` (starttime, endtime, tableid, userid) VALUES '
                       '(%s, %s, %s, %s)',
                       (request.form['starttime'], request.form['endtime'], table_id, user_id,))
        g.con.commit()
        cursor.close()
        flash("Reservierung erfolgreich!")

    return render_template('home.html', reservierungdaten=reservierungdaten, nutzerdaten=nutzerdaten,
                           tischdaten=tischdaten)


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
        cursor.execute('SELECT id, capacity FROM `table` where id = %s', (request.form["id"],))
        row = cursor.fetchone()
        cursor.close()
        if row is not None:
            flash("Tisch bereits hinzugefügt", category="error")
            return redirect(url_for('createtable'))

        cursor = g.con.cursor()
        cursor.execute('INSERT INTO `table` (id, capacity) VALUES (%s, %s)',
                       (request.form['id'],request.form['capacity'],))
        g.con.commit()
        cursor.close()
        flash('Tisch angelegt.')
    return render_template('createtable.html')

@app.route('/deletetable', methods=['GET', 'POST'])
@login_required
def deletetable():
    if request.method == 'POST':
        cursor = g.con.cursor()
        cursor.execute('SELECT id FROM `table` where id = %s', (request.form["id"],))
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            flash("Tisch existiert nicht!", category="error")
            return redirect(url_for('deletetable'))

        cursor = g.con.cursor()
        cursor.execute("DELETE FROM `table` WHERE id=%s", (request.form['id'],))
        g.con.commit()
        cursor.close()
        flash("Tisch gelöscht")
    return render_template('admin.html')


@app.route('/userdata', methods=['GET', 'POST'])
@login_required
def userdata():
    cursor = g.con.cursor()
    cursor.execute('SELECT id FROM users where name = %s', (session.get("username"),))
    row = cursor.fetchone()
    user_id = row[0]
    cursor.close()

    cursor = g.con.cursor(dictionary=True)
    if request.method == "POST":
        cursor.execute("UPDATE `users` SET name=%s, email=%s WHERE id=%s",
                       (request.form['name'], request.form['email'],
                        user_id,))
        g.con.commit()
    cursor.execute("SELECT id, name, email FROM `users` WHERE id=%s", (user_id,))
    daten = cursor.fetchone()
    cursor.close()
    flash("Erfolgreich geändert!")
    return render_template('userdata.html', htmldaten=daten)

@app.route('/changepassword', methods=['GET', 'POST'])
@login_required
def changepassword():
    if request.method == "POST":
        cursor = g.con.cursor()
        cursor.execute('SELECT id FROM users where name = %s', (session.get("username"),))
        row = cursor.fetchone()
        user_id = row[0]
        cursor.close()

        cursor = g.con.cursor()
        cursor.execute('SELECT password FROM `users` where id = %s', (user_id,))
        row2 = cursor.fetchone()
        cursor.close()
        pw_from_db = row2[0]
        if check_password_hash(pwhash=pw_from_db, password=request.form["oldpassword"]):
            if request.form['newpassword1'] == request.form['newpassword2']:
                newpassword1 = generate_password_hash(password=request.form['newpassword1'])
                cursor = g.con.cursor()
                cursor.execute("UPDATE `users` SET password=%s WHERE id=%s",
                               (newpassword1, user_id,))
                g.con.commit()
                cursor.close()
                flash("Passwort geändert")
                return redirect(url_for('login'))
            flash("Passwörter stimmen nicht überein", category="error")
            return redirect(url_for('home'))
        flash("Altes Passwort nicht korrekt", category="error")
        return redirect(url_for('home'))
    return render_template('changepassword.html')

@app.route('/deleteuser', methods=['GET','POST'])
def deleteuser():
    if request.method == 'POST':
        cursor = g.con.cursor()
        cursor.execute('SELECT id FROM `users` where id = %s', (request.form["id"],))
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            flash("Nutzer existiert nicht!", category="error")
            return redirect(url_for('deleteuser'))

        cursor = g.con.cursor()
        cursor.execute('SELECT userid FROM `reservations` where userid = %s', (request.form["id"],))
        row2 = cursor.fetchone()
        cursor.close()

        if row2 is None:
            cursor = g.con.cursor()
            cursor.execute("DELETE FROM `users` WHERE id=%s", (request.form['id'],))
            g.con.commit()
            cursor.close()
            flash("Nutzer entfernt")
            return redirect(url_for('admin'))
        flash("Zuerst Reservierung des Nutzers aufheben!", category="error")
    return render_template('deleteuser.html')

@app.route('/deletereservation', methods=['GET','POST'])
def deletereservation():
    if request.method == 'POST':
        cursor = g.con.cursor()
        cursor.execute('SELECT id FROM `reservations` where id = %s', (request.form["id"],))
        row = cursor.fetchone()
        cursor.close()

        if row is None:
            flash("Reservierung existiert nicht!", category="error")
            return redirect(url_for('deletereservation'))

        cursor = g.con.cursor()
        cursor.execute("DELETE FROM `reservations` WHERE id=%s", (request.form['id'],))
        g.con.commit()
        cursor.close()
        flash("Reservierung gelöscht")
    return render_template('deletereservation.html')

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    cursor = g.con.cursor()
    cursor.execute('SELECT id FROM users where name = %s', (session.get("username"),))
    row = cursor.fetchone()
    user_id = row[0]
    cursor.close()

    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, name, email FROM users where name = %s', (session.get("username"),))
    nutzerdaten = cursor.fetchall()
    cursor.close()

    return render_template('account.html', nutzerdaten=nutzerdaten)


# Start der Flask-Anwendung
if __name__ == '__main__':
    app.run(debug=True)

