#!/usr/bin/python3

import logging
import os

from flask import (abort, Flask, flash, redirect, render_template, request,
        session, url_for, jsonify)
from flask_oauthlib.client import OAuth
from flask_oauthlib.provider.oauth1 import OAuth1Provider
from sqlalchemy.orm.exc import NoResultFound
from login_status import login_required, get_current_user, log_user_in

import service_provider as sp
from controllers_for_sp_role import add_sp_role_controllers_to_app
from hooks import register_all_hooks
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

oauthhub_as_sp = OAuth1Provider(app)
register_all_hooks(oauthhub_as_sp)

@app.route('/user')
@login_required
def show_user():
    user = get_current_user()
    assert user is not None, "login_required didn't work??"
    if user.accesses_to_sps.count():
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
                    name = "(debug mode; saving get-name API call.)"
                return render_template('user.html', name=name, providers=authorised_services)
    return show_error_page("Got into show_user with user set to None or no associations with service providers.")

@app.route('/user/providers/remove/<provider_id>')
@login_required
def user_providers_remove(provider_id=None):
    if provider_id is None:
        return redirect(url_for('show_user'))
    user = get_current_user()
    assert user is not None, "login_required didn't work??"
    number_of_sps = user.accesses_to_sps.count()
    if number_of_sps == 0:
        flash("You have no accounts to remove.")
        return redirect(url_for('show_user'))
    elif number_of_sps == 1:
        flash("You cannot remove your last account.")
        return redirect(url_for('show_user'))
    else:
        provider = (user.accesses_to_sps
            .filter(UserSPAccess.id == provider_id)
            .one())
        db.session.delete(provider)
        db.session.commit()
        return redirect(url_for('show_user'))

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

# TODO: change URL to "/oauth/authorized" --- or better yet, "/oauth/callback"
@app.route('/oauth-authorized/<service_provider_name>/')
def oauth_authorized(service_provider_name):
    session_user = get_current_user()
    try:
        current_provider = providers.get_by_name(service_provider_name)
        token, secret = current_provider.get_access_tokens()
        fresh_user = get_user_by_token(current_provider, token, secret)
        if session_user is not None:
            if fresh_user.id == session_user.id:
                flash('This provider was already linked to this account.')
            else:
                flash('Merging accounts is not currently supported.')
        else:
            log_user_in(fresh_user)
    except ServiceProviderNotFound:
        flash('Provider not found.')
    except UserDeniedRequest:
        flash('You denied us access.')
    except UserNotFound:
        if session_user is None:
            try:
                user = get_user_by_remote_id(current_provider, token=(token,secret))
            except UserNotFound:
                user = create_user()
            log_user_in(user)
        add_SP_to_user_by_id(
            get_current_user().id, current_provider, token, secret)
    next_url = request.args.get('next') or url_for('show_user')
    return redirect(next_url)

@app.route('/login/')
def login_options():
    next_url = request.args.get('next') or url_for('show_user')
    return render_template('login.html', next_url=next_url)

add_sp_role_controllers_to_app(app, oauthhub_as_sp)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0')
