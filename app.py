#!/usr/bin/python3

import logging
import os

from flask import abort, Flask, flash, redirect, render_template, request, session, url_for
from flask_oauthlib.client import OAuth
from sqlalchemy.orm.exc import NoResultFound
from login_status import login_required, currently_logged_in, current_user_id, \
    log_user_in

import service_provider as sp
from models import db, User, UserSPAccess
from user_functions import (add_SP_to_user_by_id, create_user,
                            get_user_by_token, UserNotFound, get_user_by_remote_id)
from error_handling import show_error_page, ServiceProviderNotFound, UserDeniedRequest

app = Flask(__name__)
app.config.update({
    'DEBUG': True,
    'SECRET_KEY': 'developmentkey',
    'SQLALCHEMY_DATABASE_URI': os.getenv('SQLALCHEMY_DATABASE_URI')})

db.init_app(app)

oauth = OAuth()
providers = sp.ServiceProviderDict()
providers.add_provider(sp.Twitter(oauth))
providers.add_provider(sp.GitHub(oauth))

@app.route('/user')
@login_required
def show_user(user = None):
    if user is not None and user.accesses_to_sps.count():
        authorised_services = user.accesses_to_sps.all()

        for service_record in authorised_services:
            service_name = service_record.sp_class_name

            if service_name in providers:
                service = providers[service_name]

                # TODO potentially remove the service if it's not valid.
                if not app.config.get('DEBUG'):
                    if not service.verify():
                        continue

                    name = service.name()
                else:
                    name = None

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
        current_provider = providers.get_by_name(service_provider_name)
        token, secret = current_provider.get_access_tokens()
        user = get_user_by_token(current_provider, token, secret)

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

@app.route('/login/')
def login_options():
    next_url = request.args.get('next') or url_for('show_user')

    return render_template('login.html', next_url=next_url)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0')
