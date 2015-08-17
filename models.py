import os
from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# http://stackoverflow.com/questions/22252397/importerror-no-module-named-mysqldb
# http://stackoverflow.com/questions/2952187/getting-error-loading-mysqldb-module-no-module-named-mysqldb-have-tried-pre
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')

db = SQLAlchemy(app)

class Consumer(db.Model):
    __tablename__ = 'consumer'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(300))
    secret = db.Column(db.String(600))
    #user_accesses = db.relationship('ConsumerUserAccess',
    #        backref=db.backref('config'), lazy='dynamic')

    def __repr__(self):
        return "<Consumer(id='{}', key='{}', secret='{}')>".format(
            self.id, self.key, self.secret)

#class AccessToken(db.Model):
#    __tablename__ = 'access_tokens'
#
#    id = db.Column(db.Integer, primary_key=True)
#    token = db.Column(db.String)
#    secret = db.Column(db.String)
#    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
#    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'))
#
#    def __repr__(self):
#        return "<AccessToken(user='{}', server='{}', token='{}', secret='{}')>".format(self.user.name, self.server.name, self.token, self.secret)
#
#class OAuthServer(db.Model):
#    __tablename__ = 'servers'
#
#    id = db.Column(db.Integer, primary_key=True)
#    name = db.Column(db.String)
#
#    def __repr__(self):
#        return "<OAuthServer(name='{}')>".format(self.name)
