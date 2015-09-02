#!/usr/bin/python3

import logging

from flask import abort, Flask, flash, redirect, render_template, request, session, url_for
from flask_oauthlib.client import OAuth
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

import service_provider as sp
from models import db, User, UserSPAccess
from user_functions import add_SP_to_user, getOrCreateUser, login_required
from error_handling import show_error_page

# CONFIG
DEBUG = True
SECRET_KEY = 'developmentkey'

oauth = OAuth()
providers = sp.ServiceProviderDict()
providers.add_provider(sp.Twitter(oauth))
providers.add_provider(sp.GitHub(oauth))

app = Flask(__name__)
app.config.from_object(__name__)

db.init_app(app)

@app.route('/user')
@login_required
def show_user(user = None):
    if user is not None and user.accesses_to_sps.count():
        authorised_services = user.accesses_to_sps.all()

        for service_record in authorised_services:
            service_name = servic_record.sp_class_name

            if service_name in providers:
                service = providers[service_name]

                if not service.verify():
                    # TODO potentially remove the service if it's not valid.
                    continue

                name = service.name()
                return render_template('user.html', name=name, providers=authorised_services)

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
                        next=request.args.get('next') or request.referrer or url_for('show_user'),
                        _external=True)))
    else:
        abort(404)

@app.route('/oauth-authorized/<service_provider>/')
def oauth_authorized(service_provider):
    next_url = request.args.get('next') or url_for('show_user')

    if service_provider not in providers:
        return redirect(url_for(login))

    resp = providers[service_provider].client.authorized_response()
    if resp is None:
        flash(u'You denied the request to sign in.')
        return redirect(next_url)

    token = None
    secret = None

    if 'oauth_token' in resp:
        token = resp['oauth_token']
        secret = resp['oauth_token_secret']

    if 'access_token' in resp:
        token = resp['access_token']

    logging.info(resp)
    if 'user_id' in session:
        user = User.query.filter(User.id == session['user_id']).one()
        add_SP_to_user(user, providers[service_provider],  token, secret)
    else:
        user = getOrCreateUser(providers[service_provider], token, secret)
        session['user_id'] = user.id

    flash('You were signed in.')
    return redirect(next_url)

@app.route('/make-server')
def makeServer():
    session.clear()
    db.create_all()    
    
    return redirect(url_for('show_user'))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
