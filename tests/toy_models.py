
"""
Let's make sure we know how to use Flask-SQLAlchemy.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

SQLITE_DB_FILENAME = 'sqlite:///toy-tests.sqlite'
app = Flask(__name__)   # not actually used as an app
app.config['SQLALCHEMY_DATABASE_URI'] = SQLITE_DB_FILENAME
db = SQLAlchemy(app)

# Each shelf has zero to many products.
# Each product is only on one shelf.

class Shelf(db.Model):
    __tablename__ = 'shelf'
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200))

    def __init__(self, name):
        self.name = name

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(200))
    shelf_id = db.Column(db.Integer, db.ForeignKey('shelf.id'))
    shelf = db.relationship('Shelf',
            backref=db.backref('products', lazy='dynamic'))

    def __init__(self, name):
        self.name = name
