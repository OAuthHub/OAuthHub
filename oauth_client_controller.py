#!/usr/bin/python3

import logging
from flask import Flask, redirect, session, url_for, request, flash
from flask_oauthlib.client import OAuth
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import service_provider as sp
from models import db, User
from user_functions import getOrCreateUser

# CONFIG
DEBUG = True
SECRET_KEY = 'developmentkey'

oauth = OAuth()
providers = sp.ServiceProviderDict()
providers.add_provider(sp.Twitter(oauth))

app = Flask(__name__)
app.config.from_object(__name__)

db.init_app(app)

@app.route('/user')
def show_user():
    try:
        user = User.query.filter(User.id == session.get('user_id')).one()
    except NoResultFound:
        return 'You aren\'t logged in! <a href="' + url_for('login', service_provider='twitter') + '">login</a>'
    except MultipleResultsFound:
        logging.exception("Found too many users")
        raise

    twitter_name = providers['twitter'].name()
    return 'You are: ' + str(user.id) + '<br />Twitter Name: ' + str(twitter_name)

@app.route('/login/<service_provider>/')
def login(service_provider):
    if service_provider in providers:
        return (providers[service_provider]
                .client
                .authorize(callback=url_for(
                        'oauth_authorized',
                        service_provider = service_provider,
                        next=request.args.get('next') or request.referrer or url_for('show_user'))))

    else:
        return "Page Not found"

@app.route('/oauth-authorized/<service_provider>/')
def oauth_authorized(service_provider):
    next_url = request.args.get('next') or url_for('show_user')

    resp = providers['twitter'].client.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    user = getOrCreateUser(providers['twitter'], resp['oauth_token'], resp['oauth_token_secret'])
    session['user_id'] = user.id

    flash('You were signed in as %s' % resp['screen_name'])
    return redirect(next_url)

@app.route('/make-server')
def makeServer():
    db.create_all()    
    
    return redirect(url_for('show_user'))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
