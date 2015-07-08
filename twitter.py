#!/usr/bin/python3

# SQL stuff
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

# OAuth stuff
import clients
from flask_oauthlib.client import OAuth

# Flask stuff
from flask import Flask, redirect, session, g, url_for, request, flash

# Other
import logging

# CONFIG
DEBUG = True
SECRET_KEY = 'developmentkey'
SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

oauth = OAuth()
twitter = clients.twitter(oauth)
print(twitter)

app = Flask(__name__)
app.config.from_object(__name__)

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    fullname = db.Column(db.String)
    password = db.Column(db.String)
    authorizations = db.relationship("AccessToken", backref=db.backref("user"))

    def __repr__(self):
        return "<User(name='{}', fullname='{}', password='{}')>".format(self.name, self.fullname, self.password)

class AccessToken(db.Model):
    __tablename__ = 'access_tokens'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String)
    secret = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'))

    def __repr__(self):
        return "<AccessToken(user='{}', server='{}', token='{}', secret='{}')>".format(self.user.name, self.server.name, self.token, self.secret)

class OAuthServer(db.Model):
    __tablename__ = 'servers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)

    def __repr__(self):
        return "<OAuthServer(name='{}')>".format(self.name)

class DatabaseNotFound(RuntimeError):
    pass

@twitter.tokengetter
def get_twitter_token(token=None):
    user_id = session.get('user_id')

    latestToken = AccessToken.query.join(User)\
        .filter(User.id == user_id)\
        .order_by(db.desc(AccessToken.id))\
        .first()
    
    if latestToken is None:
        return None

    return (latestToken.token, latestToken.secret)

def createAccessToken(user, consumer, token, secret):
    pass

def getUser(server, token, secret):
    try:
        user = User.query.join(AccessToken)\
            .filter(AccessToken.server_id == server.id)\
            .filter(AccessToken.token == token)\
            .filter(AccessToken.secret == secret)\
            .one()
    except NoResultFound as nrf:
        logging.exception("Didn't find user")
        return None
    except MultipleResultsFound as mrf:
        logging.exception("Found too many users")
        raise
    
    return user

def addUser(server, token, secret):
    user = User()
    accessToken = AccessToken(server_id=server.id, token=token, secret=secret)
    user.authorizations.append(accessToken)
    db.session.add(user)
    db.session.commit()
    
    return user

def getOrCreateUser(consumer, token, secret):
    user = getUser(consumer, token, secret)

    if user is None:
        user = addUser(consumer, token, secret)
    
    return user

def getOAuthServer(resp):
    if db is None:
        raise DatabaseNotFound()

    return OAuthServer.query.filter(OAuthServer.name == 'Twitter').first()

def getTwitterAccountStatus():
    resp = twitter.get('account/verify_credentials.json')

    if resp.status == 200:
        data = resp.data
    else:
        data = None
        flash('Unable to load data from Twitter. Maybe out of '
              'API calls or Twitter is overloaded.')

    return data

@app.route('/make-server')
def makeServer():
    db.create_all()    
    server = OAuthServer(name='Twitter')
    db.session.add(server) 
    db.session.commit()
    
    return 'Created Servers.'

@app.route('/user')
def showUser():
    try:
        user = User.query.filter(User.id == session.get('user_id')).one()
    except NoResultFound as nrf:
        logging.exception("Didn't find user")
        return 'You aren\'t logged in! <a href="/login">login</a>'
    except MultipleResultsFound as mrf:
        logging.exception("Found too many users")
        raise

    twitterStatus = getTwitterAccountStatus()
    return 'You are: ' + str(user.id) + '<br />Twitter Stuff: ' + str(twitterStatus)

@app.route('/login')
def login():
    return twitter.authorize(callback=url_for('oauth_authorized',
        next=request.args.get('next') or request.referrer or None))

@app.route('/oauth-authorized')
def oauth_authorized():
    next_url = request.args.get('next') or url_for('index')
    resp = twitter.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    # For now, we only have one server
    server = getOAuthServer(resp)

    user = getOrCreateUser(server, resp['oauth_token'], resp['oauth_token_secret'])
    session['user_id'] = user.id

    flash('You were signed in as %s' % resp['screen_name'])
    return redirect(next_url)

if __name__ == "__main__":
    db.create_all()    
    app.run(host='0.0.0.0')

