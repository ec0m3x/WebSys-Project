"""Minimale Flask Anwendung"""

# Import benötigter Flask-Module
from flask import Flask, render_template, request

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
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == "POST":
        #Nutzer hat Formular abgesendet
        request.form['Nutzername']
        request.form['Passwort']
    return render_template("login.html")
@app.route('/skoch')
def skoch():
    return render_template('skoch.html')

# Start der Flask-Anwendung
if __name__ == '__main__':
    app.run(debug=True)
