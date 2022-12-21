# Import benötigter Flask-Module
from functools import wraps
from flask import Flask, render_template, request, flash, session, url_for, g, redirect
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, time
import mysql.connector

# Import der Verbindungsinformationen zur Datenbank:
# Variable DB_HOST: Servername des MySQL-Servers
# Variable DB_USER: Nutzername
# Variable DB_PASSWORD: Passwort
# Variable DB_DATABASE: Datenbankname
from db.db_credentials import DB_HOST, DB_USER, DB_PASSWORD, DB_DATABASE

app = Flask(__name__)
app.secret_key = 'irgendwas'

# Einstellungen um Mail Server zu verbinden
app.config['MAIL_SERVER'] = '141.7.63.69'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USERNAME'] = 'websys'
app.config['MAIL_PASSWORD'] = 'webmail'
app.config['MAIL_DEFAULT_SENDER'] = 'mail@example.com'

mail = Mail(app)

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


def admin_required(logged_in):
    """ Definiere View Decorator admin_required """

    @wraps(logged_in)
    def check_login(*args, **kwargs):
        """ Überprüft, ob Nutzer eingeloggt ist """
        if session.get("admin") == 1:
            # Nutzername ist in Session, Nutzer ist eingeloggt
            return logged_in(*args, **kwargs)

        # Weiterleitung zur Login Seite
        flash("Du bist nicht als Admin angemeldet! Bitte einloggen!", category="error")
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
@admin_required
def admin():
    # Alle Reservierungen als dictionary auslesen
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, capacity, starttime, endtime, tableid, userid FROM reservations', )
    reservierungdaten = cursor.fetchall()
    cursor.close()

    # Alle Nutzer als dictionaries auslesen
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, name, email FROM users', )
    nutzerdaten = cursor.fetchall()
    # print(nutzerdaten)
    cursor.close()

    # Alle Tische als dictionary auslesen
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

    # ID und E-Mail des momentan angemeldeten Users bekommen
    cursor = g.con.cursor()
    cursor.execute('SELECT id, email FROM users where name = %s', (session.get("username"),))
    row = cursor.fetchone()
    user_id = row[0]
    user_email = row[1]
    cursor.close()

    # Alle getätigten Reservierungen des Users als dictionary auslesen
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, capacity, starttime, endtime, tableid FROM `reservations` where userid = %s', (user_id,))
    reservierungdaten = cursor.fetchall()
    cursor.close()

    # Alle Nutzer als dictionary auslesen
    #cursor = g.con.cursor(dictionary=True)
    #cursor.execute('SELECT id, name, email FROM users where name = %s', (session.get("username"),))
    #nutzerdaten = cursor.fetchall()
    #cursor.close()

    # Alle Tische als dictionary auslesen
    #cursor = g.con.cursor(dictionary=True)
    #cursor.execute('SELECT capacity FROM `table`', )
    #tischdaten = cursor.fetchall()
    #cursor.close()

    if request.method == "POST":

        # Ein Tisch auslesen, das eine höhere oder gleiche Kapazität hat
        cursor = g.con.cursor(buffered=True)
        cursor.execute('SELECT id FROM `table` where capacity >= %s', (request.form["capacity"],))
        row2 = cursor.fetchone()
        cursor.close()
        # Wenn kein Tisch gefunden wird, Weiterleitung um neue Reservierung zu tätigen mit Fehlermeldung
        if row2 is None:
            flash("Kein Tisch für diese Personenanzahl gefunden!", category="error")
            return redirect(url_for('home'))
        table_id = row2[0]

        # 2 Stunden Dauer nicht überschreiten
        starttime = datetime.strptime(request.form["starttime"], '%Y-%m-%dT%H:%M')
        endtime = datetime.strptime(request.form["endtime"], '%Y-%m-%dT%H:%M')
        diff = endtime - starttime
        sec = diff.total_seconds()
        hours = sec / (60 * 60)

        # Wenn 2 Stunden Dauer überschritten wird, darf man nicht reservieren und wird auf Home weitergeleitet
        if hours > 2:
            flash("Dauer der Reservierung darf 2 Stunden nicht überschreiten!", category="error")
            return redirect(url_for('home'))

        # Überprüfen ob im Öffnungszeiten-Rahmen
        start = time(18, 0)
        end = time(23, 59)
        if start <= starttime.time() <= end and start <= endtime.time() <= end:

            # Überprüfung ob es eine Reservierung gibt, die sich mit der angegebenen Startzeit überschneidet
            cursor = g.con.cursor(buffered=True)
            cursor.execute('SELECT starttime, endtime, tableid FROM `reservations` where %s '
                           'between starttime and endtime',
                           (request.form["starttime"],))
            row3 = cursor.fetchone()

            # Überprüfung ob es eine Reservierung gibt, die sich mit der angegebenen Endzeit überschneidet
            cursor.execute('SELECT starttime, endtime, tableid FROM `reservations` where %s '
                           'between starttime and endtime',
                           (request.form["endtime"],))
            row4 = cursor.fetchone()

            # Überprüfung ob es eine Reservierung gibt, die sich mit der angegebenen Startzeit & Endzeit überschneidet
            cursor.execute('SELECT starttime, endtime, tableid FROM `reservations` '
                           'where starttime >= %s and endtime <= %s',
                           (request.form["starttime"], request.form["endtime"]))
            row5 = cursor.fetchone()
            cursor.close()

            ''' Erste Abfrage ist, ob überhaupt in einer der 3 Abfragen eine Überschneidung ist, dann wird 
            überprüft ob wenn es eine Überschneidung gibt, das man checkt, ob genau dieser Tisch schon reserviert ist'''
            if (row3 is not None or row4 is not None or row5 is not None) and \
                    (row3 is not None and table_id == row3[2] or row4 is not None and table_id == row4[2]
                     or row5 is not None and table_id == row5[2]):
                flash("Kein Tisch mit dieser Kapazität ist zur ausgewählten Uhrzeit verfügbar.", category="error")
                return redirect(url_for('home'))

            cursor = g.con.cursor()
            # Einfügen der neuen Reservierung in die Datenbank
            cursor.execute('INSERT INTO `reservations` (capacity, starttime, endtime, tableid, userid) VALUES '
                           '(%s, %s, %s, %s, %s)',
                           (request.form['capacity'], request.form['starttime'], request.form['endtime'],
                            table_id, user_id,))
            g.con.commit()
            cursor.close()

            # Senden einer Bestätigungsmail an den Kunden
            msg = Message('Reservierung', sender='lawebdelasys@mail.com',
                          recipients=[user_email])
            msg.body = f"Vielen Dank für Ihre Reservierung! \n" \
                       f"Anbei finden Sie Ihre Reservierung: \n" \
                       f"Tisch-ID: {table_id} \n" \
                       f"Personenanzahl: {request.form['capacity']} \n" \
                       f"Reservierungsbeginn: {request.form['starttime']} \n" \
                       f"Reservierungsende: {request.form['endtime']} \n" \
                       f"Wir freuen uns Sie bei uns Willkomen zu heißen! \n" \
                       f"La Web de la Sys"
            mail.send(msg)

            flash("Reservierung erfolgreich!")

            return redirect(url_for('home'))
        else:
            flash("Keine Reservierung vor 18 Uhr und nach 0 Uhr möglich", category="error")
    return render_template('home.html', reservierungdaten=reservierungdaten)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """ Login """

    if request.method == 'POST':
        cursor = g.con.cursor()
        cursor.execute('SELECT password,adminflag FROM users where name = %s', (request.form["username"],))
        row = cursor.fetchall()
        cursor.close()

        if row is None:
            flash("Nutzername existiert nicht!", category="error")
            return redirect(url_for('login'))

        pw_from_db = row[0][0]
        adminflag = row[0][1]
        if check_password_hash(pwhash=pw_from_db, password=request.form["password"]):
            # Speichern des Usernamens in der Session
            if adminflag == 1:
                flash("Admin eingeloggt")
                session['username'] = request.form['username']
                session['admin'] = 1
                return redirect(url_for('admin'))
            else:
                session['username'] = request.form['username']
                session['admin'] = 0
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
            cursor.execute('INSERT INTO users (name, email, password, adminflag) VALUES (%s, %s, %s, false)',
                           (request.form['username'], request.form['email'], password,))
            g.con.commit()
            cursor.close()

            msg = Message('Registrierung', sender='lawebdelasys@mail.com',
                          recipients=[str(request.form['email'])])
            msg.body = f"Vielen Dank, dass Sie sich bei uns registriert haben. \n" \
                       f"Anbei finden Sie Ihre Informationen: \n" \
                       f"Nutzername: {request.form['username']} \n" \
                       f"E-Mail: {request.form['email']} \n" \
                       f"Auf eine baldige Reservierung! \n" \
                       f"La Web de la Sys"
            mail.send(msg)

            flash("Konto angelegt!")
            return redirect(url_for('index'))
        flash("Passwörter stimmen nicht überein!", category="error")
    return render_template("sign_up.html")


@app.route('/logout')
@login_required
def logout():
    session.clear()
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
        cursor.execute('INSERT INTO `table` (capacity) VALUES (%s)',
                       (request.form['capacity'],))
        g.con.commit()
        cursor.close()
        flash('Tisch angelegt.')
    return render_template('createtable.html')


@app.route('/userdata', methods=['GET', 'POST'])
@login_required
def userdata():

    # Rausfinden der ID des momentan angemeldeten Users
    cursor = g.con.cursor()
    cursor.execute('SELECT id FROM users where name = %s', (session.get("username"),))
    row = cursor.fetchone()
    user_id = row[0]
    cursor.close()

    cursor = g.con.cursor(dictionary=True)
    if request.method == "POST":
        # Überprüfen, ob Username schon vergeben
        if request.form["name"] != session.get('username'):
            cursor.execute('SELECT name FROM users where name = %s', (request.form["name"],))
            row = cursor.fetchone()
            if row is not None:
                flash("Benutzername ist bereits vergeben", category="error")
                return redirect(url_for('userdata'))

        cursor.execute('SELECT email FROM users where name = %s', (session.get("username"),))
        row2 = cursor.fetchone()
        e_mail = row2['email']
        # Überprüfen, on Email schon vergeben
        if request.form["email"] != e_mail:
            cursor.execute('SELECT email FROM users where email = %s', (request.form["email"],))
            row = cursor.fetchone()
            if row is not None:
                flash("Email ist bereits vergeben", category="error")
                return redirect(url_for('userdata'))
        cursor.execute("UPDATE `users` SET name=%s, email=%s WHERE id=%s",
                       (request.form['name'], request.form['email'],
                        user_id,))
        g.con.commit()
        session['username'] = request.form['name']
        flash("Erfolgreich geändert!")
    cursor.execute("SELECT id, name, email FROM `users` WHERE id=%s", (user_id,))
    daten = cursor.fetchone()
    cursor.close()
    return render_template('userdata.html', htmldaten=daten)


@app.route('/changepassword', methods=['GET', 'POST'])
@login_required
def changepassword():
    if request.method == "POST":

        # Rausfinden der ID des momentan angemeldeten Users
        cursor = g.con.cursor()
        cursor.execute('SELECT id FROM users where name = %s', (session.get("username"),))
        row = cursor.fetchone()
        user_id = row[0]

        # Rausfinden des Passworts des momentan angemeldeten Users
        cursor.execute('SELECT password FROM `users` where id = %s', (user_id,))
        row2 = cursor.fetchone()
        cursor.close()
        pw_from_db = row2[0]

        # Überprüfen, ob Passwort mit eingegebenem Passwort übereinstimmt
        if check_password_hash(pwhash=pw_from_db, password=request.form["oldpassword"]):
            # Überprüfen, ob neues Passwort mit Bestätigung des Passwortes übereinstimmt
            if request.form['newpassword1'] == request.form['newpassword2']:
                # Überprüfen, ob neues Passwort, das alte Passwort ist
                if check_password_hash(pwhash=pw_from_db, password=request.form["newpassword1"]):
                    flash("Neues Passwort darf nicht mit altem Passwort übereinstimmen", category="error")
                    return redirect(url_for('changepassword'))
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



@app.route('/changereservation/<myid>', methods=['GET', 'POST'])
@login_required
def changereservation(myid):

    # Rausfinden der ID des momentan angemeldeten Users
    cursor = g.con.cursor()
    cursor.execute('SELECT id FROM users where name = %s', (session.get("username"),))
    row = cursor.fetchone()
    user_id = row[0]
    cursor.close()

    # Rausfinden der Reservierung, die geändert werden soll
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, capacity, starttime, endtime, tableid FROM `reservations` where id = %s', (myid,))
    daten = cursor.fetchone()
    cursor.close()
    # Zwischenspeicherung der Reservierung
    mycapacity = daten['capacity']
    mystarttime = daten['starttime']
    myendtime = daten['endtime']
    mytable = daten['tableid']

    if request.method == "POST":
        cursor = g.con.cursor()
        cursor.execute('DELETE FROM `reservations` WHERE id=%s', (myid,))
        cursor.close()

        cursor = g.con.cursor(buffered=True)
        cursor.execute('SELECT id FROM `table` where capacity >= %s', (request.form["capacity"],))
        row2 = cursor.fetchone()
        cursor.close()
        if row2 is None:
            flash("Kein Tisch für diese Personenanzahl gefunden!", category="error")
            return redirect(url_for('home'))
        table_id = row2[0]

        # 2 Stunden Dauer nicht überschreiten
        starttime = datetime.strptime(request.form["starttime"], '%Y-%m-%dT%H:%M')
        endtime = datetime.strptime(request.form["endtime"], '%Y-%m-%dT%H:%M')
        diff = endtime - starttime
        sec = diff.total_seconds()
        hours = sec / (60 * 60)

        if hours > 2:
            flash("Dauer der Reservierung darf 2 Stunden nicht überschreiten!", category="error")
            return redirect(url_for('home'))

        # Überprüfen ob im Öffnungszeiten-Rahmen
        start = time(18, 0)
        end = time(23, 59)
        if start <= starttime.time() <= end and start <= endtime.time() <= end:

            cursor = g.con.cursor(buffered=True)
            # Nimmt alle Reservierungen wo die Startzeit zwischen einer anderen Reservierung liegt
            cursor.execute('SELECT starttime, endtime, tableid FROM `reservations` where %s '
                           'between starttime and endtime',
                           (request.form["starttime"],))
            row3 = cursor.fetchone()
            cursor.execute('SELECT starttime, endtime, tableid FROM `reservations` where %s '
                           'between starttime and endtime',
                           (request.form["endtime"],))
            row4 = cursor.fetchone()
            cursor.execute('SELECT starttime, endtime, tableid FROM `reservations` '
                           'where starttime >= %s and endtime <= %s',
                           (request.form["starttime"], request.form["endtime"]))
            row5 = cursor.fetchone()
            cursor.close()

            if (row3 is not None or row4 is not None or row5 is not None) and \
                    (row3 is not None and table_id == row3[2] or row4 is not None and table_id == row4[2]
                     or row5 is not None and table_id == row5[2]):
                cursor = g.con.cursor()
                cursor.execute('INSERT INTO `reservations` (capacity, starttime, endtime, tableid, userid) VALUES '
                           '(%s, %s, %s, %s, %s)',
                           (mycapacity, mystarttime, myendtime, mytable, user_id))
                cursor.close()
                flash("Kein Tisch mit dieser Kapazität ist zur ausgewählten Uhrzeit verfügbar.", category="error")
                return redirect(url_for('home'))

            cursor = g.con.cursor()
            cursor.execute('INSERT INTO `reservations` (capacity, starttime, endtime, tableid, userid) VALUES '
                           '(%s, %s, %s, %s, %s)',
                           (request.form['capacity'], request.form['starttime'], request.form['endtime'],
                            table_id, user_id,))
            g.con.commit()
            cursor.close()
            flash("Reservierung erfolgreich geändert!")
            return redirect(url_for('home'))
        else:
            flash("Keine Reservierung vor 18 Uhr und nach 0 Uhr möglich", category="error")
    return render_template('changereservation.html', daten=daten)

@app.route('/deleteres', methods=['GET', 'POST'])
@login_required
def deleteres():
    cursor = g.con.cursor()
    if request.method == 'POST':
        if request.form.getlist('checkbox'):
            # Löscht alle Reservierungen, die mit der Checkbox ausgewählt wurden
            for getid in request.form.getlist('checkbox'):
                cursor.execute("DELETE FROM `reservations` WHERE id=%s", (getid,))
                g.con.commit()
            cursor.close()
            flash("Reservierung gelöscht")
        else:
            flash("Nichts zum Löschen ausgewählt!", category='error')
        if session.get('admin') == 1:
            return redirect(url_for('admin'))
        else:
            return redirect(url_for('home'))
    return render_template('home.html')


@app.route('/deleteuser', methods=['GET', 'POST'])
@admin_required
def deleteuser():
    cursor = g.con.cursor()
    if request.method == 'POST':
        if request.form.getlist('checkbox'):
            # Löscht alle User, die mit der Checkbox ausgewählt wurden
            for getid in request.form.getlist('checkbox'):
                cursor.execute("DELETE FROM `users` WHERE id=%s", (getid,))
                g.con.commit()
            cursor.close()
            flash("Nutzer gelöscht")
        else:
            flash("Nichts zum Löschen ausgewählt!", category='error')
        return redirect(url_for('admin'))
    return render_template('admin.html')


@app.route('/deletetable', methods=['GET', 'POST'])
@admin_required
def deletetable():
    cursor = g.con.cursor()
    if request.method == 'POST':
        if request.form.getlist('checkbox'):
            # Löscht alle Tische, die mit der Checkbox ausgewählt wurden
            for getid in request.form.getlist('checkbox'):
                cursor.execute("DELETE FROM `table` WHERE id=%s", (getid,))
                g.con.commit()
            cursor.close()
            flash("Tisch gelöscht")
        else:
            flash("Nichts zum Löschen ausgewählt!", category='error')
        return redirect(url_for('admin'))
    return render_template('admin.html')


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():

    # Auslesen der Userdaten als dictionary
    cursor = g.con.cursor(dictionary=True)
    cursor.execute('SELECT id, name, email FROM users where name = %s', (session.get("username"),))
    nutzerdaten = cursor.fetchall()
    cursor.close()

    return render_template('account.html', nutzerdaten=nutzerdaten)

@app.route('/help', methods=['GET', 'POST'])
def help():
    return render_template('help.html')

@app.route('/contactform', methods=['GET', 'POST'])
def contactform():
    if request.method == 'POST':
        msg = Message(request.form['art'], sender=str(request.form['email']), recipients=['labwedelasys@mail.com'])
        msg.body = f"{request.form['name']}, {request.form['text']}"
        mail.send(msg)
        flash('Abgeschickt')
        return redirect(url_for('contactform'))
    return render_template('contactform.html')

@app.route('/deleteacc', methods=['GET', 'POST'])
@login_required
def deleteacc():
    cursor = g.con.cursor()
    cursor.execute('SELECT email FROM users where name = %s', (session.get("username"),))
    row = cursor.fetchone()
    user_email = row[0]
    cursor.close()
    if request.method == 'POST':
        msg = Message('Kontolöschung', sender=str(user_email), recipients=['lawebdelasys@mail.com'])
        msg.body = f"{session.get('username')} möchte Konto löschen."
        mail.send(msg)
        flash('Kontolöschung erfolgreich beantragt! Wir melden uns bei Ihnen.')
        return redirect(url_for('account'))
    return render_template('account.html')
def get_reset_token(email):
    # Erstellung einer URL als Zurücksetzung des Passworts
    s = URLSafeTimedSerializer(app.secret_key)
    token = s.dumps(email, salt='email-confirm')
    return token
@app.route('/resetpassword', methods=['GET', 'POST'])
@login_required
def resetpassword():
    if request.method == 'POST':
        #Überprüfe, ob die Email existiert
        cursor = g.con.cursor()
        cursor.execute('SELECT id FROM users where email = %s', (request.form['email'],))
        row = cursor.fetchone()
        cursor.close()
        if row:
            token = get_reset_token(request.form['email'])
            # Schicke eine Mail an die Email, wenn sie existiert mit einem generierten Link
            msg = Message('Passwortzurücksetzung', sender='lawebdelasys@mail.com',
                          recipients=[str(request.form['email'])])
            link = url_for('confirmmail', token=token, _external=True)
            msg.body = f"Hier ist der Link zum Zurücksetzen des Passworts: \n {link} \n" \
                       f"Rufen Sie diesen bitte innerhalb von 2 Minuten auf und erstellen ein neues Passwort."
            mail.send(msg)
            flash("Die Mail zum Zurücksetzen des Passworts wurde verschickt.")
        else:
            flash('Es existiert kein Konto mit dieser E-Mail Adresse!', category='error')
            return redirect('resetpassword')
    return render_template('resetpassword.html')


@app.route('/confirmmail/<token>', methods=['GET', 'POST'])
@login_required
def confirmmail(token):
    try:
        # Überprüfung der generierten URL innerhalb von 2 Minuten
        s = URLSafeTimedSerializer(app.secret_key)
        email = s.loads(token, salt='email-confirm', max_age=120)
    except SignatureExpired:
        flash("Der Link ist abgelaufen!", category="error")
        return redirect(url_for('login'))
    if request.method == 'POST':

        cursor = g.con.cursor()
        cursor.execute('SELECT password FROM `users` where email = %s', (email,))
        row2 = cursor.fetchone()
        cursor.close()
        pw_from_db = row2[0]

        if request.form['newpassword1'] == request.form['newpassword2']:
            if check_password_hash(pwhash=pw_from_db, password=request.form["newpassword1"]):
                flash("Neues Passwort darf nicht mit altem Passwort übereinstimmen", category="error")
                return redirect(url_for('confirmmail'))
            newpassword1 = generate_password_hash(password=request.form['newpassword1'])
            cursor = g.con.cursor()
            cursor.execute("UPDATE `users` SET password=%s WHERE email=%s",
                           (newpassword1, email,))
            g.con.commit()
            cursor.close()
            flash("Passwort gesetzt")
            return redirect(url_for('login'))
        flash("Passwörter stimmen nicht überein", category="error")
        return redirect(url_for('confirmmail'))
    return render_template('confirmmail.html')

# Start der Flask-Anwendung
if __name__ == '__main__':
    app.run(debug=True)
