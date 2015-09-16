from os import getenv
import logging

from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import gen_salt

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = getenv('SQLALCHEMY_DATABASE_URI')
    db.init_app(app)
    return app

class Consumer(db.Model):
    __tablename__ = 'consumer'

    id = db.Column(db.Integer, primary_key=True)
    client_key = db.Column(db.String(300))
    client_secret = db.Column(db.String(600))
    accesses_to_users = db.relationship('ConsumerUserAccess',
            backref=db.backref('consumer'), lazy='dynamic')
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship('User',
            backref=db.backref('api_apps', lazy='dynamic'))
    _redirect_uris = db.Column(db.Text)
    _realms = db.Column(db.Text)

    def __init__(self, creator, client_key, client_secret, redirect_uris, realms):
        if (any(' ' in uri for uri in redirect_uris) or
                any(' ' in r for r in realms)):
            raise ValueError("redirect_uris and realms do not allow spaces.")
        self.creator = creator
        self.client_key = client_key
        self.client_secret = client_secret
        self._redirect_uris = ' '.join(redirect_uris)
        self._realms = ' '.join(realms)

    def __repr__(self):
        return "<Consumer(id={!r}, client_key={!r}, client_secret={!r})>".format(
                self.id, self.client_key, self.client_secret)

    @property
    def redirect_uris(self):
        return self._redirect_uris.split(' ')

    @property
    def realms(self):
        return self._realms.split(' ')

    @property
    def default_redirect_uri(self):
        return self.redirect_uris[0]

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
    client_id = db.Column(db.Integer, db.ForeignKey('consumer.id'))
    client = db.relationship('Consumer')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')
    realms = db.Column(db.Text)
    token = db.Column(db.String(1000))
    secret = db.Column(db.String(2000))

    def __init__(self, client, user, realms, token, secret):
        """

        :param client: Consumer
        :param user: User
        :param realms: list of str
        :param token: str
        :param secret: str
        :return:
        """
        self.client = client
        self.user = user
        self.realms = list(realms)
        self.token = token
        self.secret = secret

    def __repr__(self):
        return ("<ConsumerUserAccess(client={}, user={}, realms={}, "
                "token={!r}, secret={!r})>").format(
            self.client, self.user, self.realms,
            self.token, self.secret)

    @property
    def client_key(self):
        return self.client.client_key


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

class RequestToken(db.Model):
    __tablename__ = 'request_token'

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('consumer.id'))
    client = db.relationship('Consumer')    # Does this work?
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User')          # Does this work?
    redirect_uri = db.Column(db.String(2000))
    realms = db.Column(db.Text)
    token = db.Column(db.String(1000))
    secret = db.Column(db.String(2000))
    verifier = db.Column(db.String(2000))

    def __init__(self, client, token, secret, redirect_uri, realms, user=None):
        # I'm probably far too defensive here. -- Zong
        if not all((
                isinstance(client, Consumer),
                isinstance(token, str),
                isinstance(secret, str),
                isinstance(redirect_uri, str),
                (isinstance(realms, list) or isinstance(realms, tuple)),
                realms,
                isinstance(realms[0], str))):
            log.debug("RequestToken.__init__ received: {}".format((
                client, token, secret, redirect_uri, realms, user)))
            raise ValueError("Check your arguments in the DEBUG log.")
        self.client = client
        self.user = user  # At first RT's have no associated user.
        self.redirect_uri = redirect_uri
        self.realms = list(realms)
        self.token = token
        self.secret = secret
        self.verifier = gen_salt(40)

    def __repr__(self):
        return ("<RequestToken(client={}, user={}, "
                "redirect_uri={!r}, realms={}, "
                "token={!r}, secret={!r}, verifier={!r})>").format(
                    self.client, self.user, self.redirect_uri, self.realms,
                    self.token, self.secret, self.verifier)

    @property
    def client_key(self):
        return self.client.client_key

class Nonce(db.Model):
    __tablename__ = 'nonce'

    id = db.Column(db.Integer, primary_key=True)
    client_key = db.Column(db.String(300))
    timestamp = db.Column(db.Integer)
    nonce = db.Column(db.String(2000))
    request_token = db.Column(db.String(1000))
    access_token = db.Column(db.String(1000))

    def __init__(self, client_key, timestamp, nonce,
            request_token, access_token):
        self.client_key = client_key
        self.timestamp = timestamp
        self.nonce = nonce
        self.request_token = request_token
        self.access_token = access_token

    def __repr__(self):
        return ("<Nonce(client_key={!r}, timestamp={!r}, nonce={!r}, "
                "request_token={!r}, access_token={!r})>").format(
                    self.client_key, self.timestamp, self.nonce,
                    self.request_token, self.access_token)
