#!/usr/bin/python3

import logging

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_oauthlib.client import OAuth
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import service_provider as sp
from models import db, User, UserSPAccess
from user_functions import getOrCreateUser, login_required
from error_handling import show_error_page

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
@login_required
def show_user(user = None):
    if user is not None and user.accesses_to_sps.count():
        service_name = user.accesses_to_sps.first().sp_class_name

        if service_name in providers:
            name = providers[service_name].name()
            return render_template('user.html', name=name, providers=user.accesses_to_sps.all())

    return show_error_page("Got into show_user with user set to None or no associations with service providers.")

@app.route('/user/providers/remove/<provider_id>')
@login_required
def user_providers_remove(provider_id = None, user = None):
    if provider_id is None:
        return redirect(url_for('show_user'))

    number_of_sps = user.accesses_to_sps.count()

    if number_of_sps == 0:
        flash("You have no accounts to remove.")
        return redirect(url_for('show_user'))

    if number_of_sps == 1:
        flash("You cannot remove your last account.")
        return redirect(url_for('show_user'))

    if user is not None and user.accesses_to_sps.count():
        provider = user.accesses_to_sps.filter(UserSPAccess.id == provider_id).one()

        db.session.delete(provider)
        db.session.commit()

        return redirect(url_for('show_user'))

    return show_error_page("Got into show_user with user set to None or no associations with service providers.")

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

    if service_provider not in providers:
        return redirect(url_for(login))

    resp = providers[service_provider].client.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    user = getOrCreateUser(providers[service_provider], resp['oauth_token'], resp['oauth_token_secret'])
    session['user_id'] = user.id

    flash('You were signed in as %s' % resp['screen_name'])
    return redirect(next_url)

@app.route('/make-server')
def makeServer():
    db.create_all()    
    
    return redirect(url_for('show_user'))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
