#!/usr/bin/python3

# SQL stuff
from models import db, User, AccessToken, OAuthServer
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

# OAuth stuff
import clients
from flask_oauthlib.client import OAuth

# Flask stuff
from flask import Flask, redirect, session, g, url_for, request, flash

# Other
import logging
from user_functions import getOrCreateUser

# CONFIG
DEBUG = True
SECRET_KEY = 'developmentkey'
SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

oauth = OAuth()
twitter = clients.twitter(oauth)

app = Flask(__name__)
app.config.from_object(__name__)

db.init_app(app)

class DatabaseNotFound(RuntimeError):
    pass

def createAccessToken(user, consumer, token, secret):
    pass

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
    
    return redirect(url_for('showUser'))

@app.route('/user')
def showUser():
    try:
        user = User.query.filter(User.id == session.get('user_id')).one()
    except NoResultFound as nrf:
        logging.exception("Didn't find user")
        return 'You aren\'t logged in! <a href="/login?next=user">login</a>'
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

    user = getOrCreateUser(db, server, resp['oauth_token'], resp['oauth_token_secret'])
    session['user_id'] = user.id

    flash('You were signed in as %s' % resp['screen_name'])
    return redirect(next_url)

if __name__ == "__main__":
    app.run(host='0.0.0.0')

