#!/usr/bin/python3

import logging
import os

from flask import Flask
from flask_oauthlib.client import OAuth
from flask_oauthlib.provider.oauth1 import OAuth1Provider
from sqlalchemy.orm.exc import NoResultFound

from controllers_for_sp_role import add_sp_role_controllers_to_app
from controllers_for_client_role import add_client_role_controllers_to_app
from controllers_for_ui import add_ui_controllers_to_app
from hooks import register_all_hooks
from models import db
import service_provider as sp

app = Flask(__name__)
app.config.update({
    'DEBUG': True,
    'SECRET_KEY': 'developmentkey',
    'SQLALCHEMY_DATABASE_URI': os.getenv('SQLALCHEMY_DATABASE_URI')})

db.init_app(app)

oauthhub_as_sp = OAuth1Provider(app)
register_all_hooks(oauthhub_as_sp)

add_sp_role_controllers_to_app(app, oauthhub_as_sp)

oauth = OAuth()
providers = sp.ServiceProviderDict()
providers.add_provider(sp.Twitter(oauth))
providers.add_provider(sp.GitHub(oauth))

add_client_role_controllers_to_app(app, providers)

add_ui_controllers_to_app(app, providers)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0')
