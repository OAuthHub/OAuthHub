from os import getenv

from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
    db.init_app(app)
    return app

class Consumer(db.Model):
    __tablename__ = 'consumer'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(300))
    secret = db.Column(db.String(600))
    accesses_to_users = db.relationship('ConsumerUserAccess',
            backref=db.backref('consumer'), lazy='dynamic')

    def __init__(self, key=None, secret=None):
        self.key = key
        self.secret = secret

    def __repr__(self):
        return "<Consumer(id='{}', key='{}', secret='{}')>".format(
                self.id, self.key, self.secret)

class User(db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    accesses_from_consumers = db.relationship('ConsumerUserAccess',
            backref=db.backref('user'), lazy='dynamic')
    accesses_to_sps = db.relationship('UserSPAccess',
            backref=db.backref('user'), lazy='dynamic')

    def __init__(self, name=None):
        '''
        :param name: A human-friendly user name. Unicode should be fine.
        '''
        self.name = name

    def __repr__(self):
        return "<User(name='{}')>".format(self.name)

class ConsumerUserAccess(db.Model):
    __tablename__ = 'consumer_user_access'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(1000))
    secret = db.Column(db.String(2000))
    consumer_id = db.Column(db.Integer, db.ForeignKey('consumer.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, token=None, secret=None):
        self.token = token
        self.secret = secret

    def __repr__(self):
        return ("<ConsumerUserAccess(id='{}', token='{}', " +
                "secret='{}', consumer='{}'), user='{}'>").format(
                self.id, self.token, self.secret, self.consumer, self.user)

class UserSPAccess(db.Model):
    __tablename__ = 'user_sp_access'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(1000))
    secret = db.Column(db.String(2000))
    sp_class_name = db.Column(db.String(300))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    remote_user_id = db.Column(db.Integer)

    def __init__(self, token=None, secret=None, sp_class_name=None, user=None):
        """
        :param sp_class_name: A string that shoule be ok to eval. Yes, stringly-typed.
        """
        self.token = token
        self.secret = secret
        self.sp_class_name = sp_class_name
        self.user_id = None if user is None else user.id

    def __repr__(self):
        return ('<UserSPAccess(token="{}", secret="{}", ' +
                    'sp_class_name="{}", user_id="{}">').format(self.token,
                        self.secret, self.sp_class_name, self.user_id)
