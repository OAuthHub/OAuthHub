#!/usr/bin/python3

import logging

from flask import abort, Flask, flash, redirect, render_template, request, session, url_for
from flask_oauthlib.client import OAuth
from sqlalchemy.orm.exc import NoResultFound

import service_provider as sp
from models import db, User, UserSPAccess
from user_functions import add_SP_to_user_by_id, create_user, currently_logged_in, getUser, log_user_in, login_required, UserNotFound, get_user_by_remote_id
from error_handling import show_error_page, ServiceProviderNotFound, UserDeniedRequest

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
            service_name = service_record.sp_class_name

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
                        service_provider_name = service_provider,
                        next=request.args.get('next') or request.referrer or url_for('show_user'),
                        _external=True)))
    else:
        abort(404)

@app.route('/oauth-authorized/<service_provider_name>/')
def oauth_authorized(service_provider_name):
    try:
        current_provider = get_service_provider(service_provider_name)
        token, secret = get_access_tokens(current_provider)
        user = getUser(current_provider, token, secret)

        if currently_logged_in():
            if user.id == current_user_id():
                flash('This provider was already linked to this account.')
            else:
                flash('Merging accounts is not currently supported.')
        else:
            log_user_in(user)

    except ServiceProviderNotFound:
        flash('Provider not found.')

    except UserDeniedRequest:
        flash('You denied us access.')

    except UserNotFound:
        if not currently_logged_in():
            try:
                user = get_user_by_remote_id(current_provider, token=(token,secret))
            except UserNotFound:
                user = create_user()
            log_user_in(user)

        add_SP_to_user_by_id(session['user_id'], current_provider, token, secret)

    next_url = request.args.get('next') or url_for('show_user')
    return redirect(next_url)

def get_service_provider(name):
    if name not in providers:
        raise ServiceProviderNotFound()

    return providers[name]

def get_access_tokens(provider):
    resp = provider.client.authorized_response()
    if resp is None:
        raise UserDeniedRequest()

    return extract_tokens(resp)

def extract_tokens(resp):
    token = None
    secret = None

    if 'oauth_token' in resp: # OAuth1
        token = resp['oauth_token']
        secret = resp['oauth_token_secret']
    elif 'access_token' in resp: # OAuth2
        token = resp['access_token']

    return (token, secret)

@app.route('/make-server')
def makeServer():
    session.clear()
    db.create_all()

    return redirect(url_for('show_user'))

if __name__ == "__main__":
    app.run(host='0.0.0.0')
