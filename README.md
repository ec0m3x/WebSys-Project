# Webbasierte Systeme - Gruppe 06

Entwicklung einer Flask-Anwendung mit Datenbankanbindung

# Online Tischreservierung "Le Web de la Sys"

https://ws-2022-06.websys.win.hs-heilbronn.de
## Benötigte Module
* **Flask**
* **Flask-Login**
* **mysql-python-connector**
* **flask-SQLAlchemy**

## Projektstruktur

Der Projektordner enthält standardmäßig folgende Dateien und Verzeichnisse:

* **db**:
  * **db_credentials.py**: enthält Verbindungsinformationen zur Datenbank
  * **db_init.py**: Python-Skript zur Erstellung der Projektdatenbank
  * **db_schema.sql**: enthält SQL-Befehle zur Erzeugung der Datenbank
* **static**:
  * enthält alle statischen Dateien wie CSS-Dateien und Bilder
* **templates**:
  * enthält alle HTML-Templates
* **.gitignore**: enthält alle Dateien und Verzeichnisse, die nicht in die Versionskontrolle mit Git aufgenommen werden sollen
* **LICENSE**: enthält Lizenzbedingungen für das gesamte Projekt
* **README.md**: Diese Datei, enthält die Projektdokumentation im Markdown-Format
* **ws-2022-06.py**: enthält die eigentliche Flask-Anwendung

## Projektanforderungen

### Mindestanforderungen

* [ ] Nutzer-Registration: Vor- & Nachname, Anschrift, Geburtsdatum, E-Mail, Benutzername, Telefonnummer, Passwort
* [ ] Nutzer-Login: Benutzername, Passwort 
* [ ] Admin-Bereich mit Daten- und Nutzerverwaltung: Benutzername, Passwort
* [ ] Einfügen, Ändern und Löschen von Daten: Jeder Nutzer sollte nur seine eigenen Daten (persönliche Informationen, als auch Reservierungen), Admin alle Daten bearbeiten können (Freie Termine/Tische hinzufügen, Nutzer löschen, Tischreservierung auflösen)
* [ ] Als Anwender Reservierungen tätigen, bearbeiten und löschen: Tag, Uhrzeit, Personenanzahl
* [ ] Übersicht anzeigen über alle getätigten Reservierungen als Nutzer/Admin 
* [ ] Navigationsleiste

### Optionale Anforderungen

* [ ] Passwortzurücksetzung-/änderung
* [ ] Nutzer-Login: gebunden mit E-Mail und Passwort
* [ ] Übersicht über Verfügbarkeiten
* [ ] Suchfunktion
* [ ] Standortermittlung
* [ ] Kontaktformular
* [ ] Speisekarte 
