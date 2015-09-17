
""" A self-contained OAuthHub Consumer app

Yeah.

"""

import os
from functools import wraps
import logging

from flask import Flask, request, session, url_for, redirect, render_template
from werkzeug.security import gen_salt
from flask_oauthlib.client import OAuth

CONSUMER_KEY = os.environ['OAUTHHUB_CONSUMER_KEY']
CONSUMER_SECRET = os.environ['OAUTHHUB_CONSUMER_SECRET']

BASE_URL='http://oauthhub.servehttp.com/api/v1/'
REQUEST_TOKEN_URL='http://oauthhub.servehttp.com/oauth/request-token'
ACCESS_TOKEN_URL='http://oauthhub.servehttp.com/oauth/access-token'
AUTHORIZE_URL='http://oauthhub.servehttp.com/oauth/authorize'

log = logging.getLogger(__name__)

class User:

    def __init__(self, name, id_=None):
        """ Create new (volatile) user object

        :param name: str
        :param id_: str
        :return:
        """
        if id_ is None:
            id_ = gen_salt(40)
            while id_ in users:
                id_ = gen_salt(40)
        self.id = id_
        self.name = name

users = dict()

def save_user(user):
    users[user.id] = user

def load_user(user_id):
    return users[user_id]

def get_access_token():
    return session.get('token_credentials')

def set_access_token(token, secret):
    session['token_credentials'] = token, secret

def del_access_token():
    if 'token_credentials' in session:
        del session['token_credentials']

def log_user_in(user):
    session['user_id'] = user.id

def log_user_out():
    if 'user_id' in session:
        del session['user_id']

def get_current_user():
    uid = session.get('user_id')
    if uid is None:
        return None
    else:
        try:
            return users[uid]
        except KeyError as e:
            log.exception(e)
            log.debug("Current users: {}".format(users))
            return None

def login_required(c):
    @wraps(c)
    def first_check(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for(
                'login',
            ))
        else:
            return c(*args, **kwargs)
    return first_check

def create_app():
    app = Flask(
        __name__,
        template_folder='example_consumer_templates')
    app.config.update({
        'DEBUG': True,
        'SECRET_KEY': 'lol-secret-key',
    })
    oauth = OAuth(app)
    oauthhub = oauth.remote_app(
        'oauthhub',
        consumer_key=CONSUMER_KEY,
        consumer_secret=CONSUMER_SECRET,
        request_token_params={
            'realm': 'read'},
        base_url=BASE_URL,
        request_token_url=REQUEST_TOKEN_URL,
        access_token_method='GET',
        access_token_url=ACCESS_TOKEN_URL,
        authorize_url=AUTHORIZE_URL)
    oauthhub.tokengetter(get_access_token)

    @app.route('/')
    def index():
        current_user = get_current_user()
        log.debug("Index page found session user: {!r}".format(
            current_user))
        if current_user is None:
            return render_template('login.html')
        else:
            return render_template(
                'user.html',
                user=current_user)

    @app.route('/login/')
    def login():
        return oauthhub.authorize(
            callback=url_for(
                'callback',
                #next=request.args.get('next') or url_for('index'),
                _external=True))

    @app.route('/oauth-callback')
    def callback():
        authorized_response = oauthhub.authorized_response()
        if authorized_response is None:
            return '''You denied us access.'''
        else:
            at = authorized_response['oauth_token']
            ats = authorized_response['oauth_token_secret']
            set_access_token(at, ats)
            user_resp = oauthhub.get('user.json')
            log.debug("user_resp: {!r}".format(user_resp))
            data = user_resp.data
            log.debug("user_resp.data: {!r}".format(data))
            user = User(data['name'])
            save_user(user)
            log_user_in(user)
            return redirect(url_for('index'))

    @app.route('/logout/')
    def logout():
        log_user_out()
        return redirect(url_for('index'))

    return app

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app = create_app()
    app.run(host='0.0.0.0', port=8000)
