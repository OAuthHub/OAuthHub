import os
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
db = SQLAlchemy(app)

class Consumer(db.Model):
    __tablename__ = 'consumer'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(300))
    secret = db.Column(db.String(600))
    user_accesses = db.relationship('ConsumerUserAccess',
            backref=db.backref('consumer'), lazy='dynamic')

    def __init__(self, key=None, secret=None):
        self.key = key
        self.secret = secret

    def __repr__(self):
        return "<Consumer(id='{}', key='{}', secret='{}')>".format(
                self.id, self.key, self.secret)

class ConsumerUserAccess(db.Model):
    __tablename__ = 'consumer_user_access'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(1000))
    secret = db.Column(db.String(2000))
    consumer_id = db.Column(db.Integer, db.ForeignKey('consumer.id'))
    #user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, token=None, secret=None):
        self.token = token
        self.secret = secret

    def __repr__(self):
        return ("<ConsumerUserAccess(id='{}', token='{}', " +
                "secret='{}', consumer='{}'), user='{}'>").format(
                self.id, self.token, self.secret, self.consumer,)

def do():
    ''' Save some typing in the REPL.
    '''
    c = Consumer('CK', 'CS')
    a = ConsumerUserAccess('AT', 'AS')
    return c, a

#class OAuthServer(db.Model):
#    __tablename__ = 'servers'
#
#    id = db.Column(db.Integer, primary_key=True)
#    name = db.Column(db.String)
#
#    def __repr__(self):
#        return "<OAuthServer(name='{}')>".format(self.name)
