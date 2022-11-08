from . import db
from flask_login import UserMixin

# from datetime import datetime

DEFAULT_RESERVATION_LENGTH = 1  # Eine Stunde
MAX_TABLE_CAPACITY = 6



class Guest(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), index=True)
    last_name = db.Column(db.String(50), index=True)
    email = db.Column(db.String(50), index=True, unique=True)
    password = db.Column(db.String(50))


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    capacity = db.Column(db.Integer, index=True)


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'))
    guest = db.relationship('Guest')
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'))
    table = db.relationship('Table')
    num_guests = db.Column(db.Integer, index=True)
    reservation_time = db.Column(db.DateTime, index=True)
