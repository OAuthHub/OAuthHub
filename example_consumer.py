
""" A self-contained OAuthHub Consumer app

Yeah.

"""

from functools import wraps

from flask import Flask, request, session, url_for, redirect, render_template
from werkzeug.security import gen_salt
from flask_oauthlib.client import OAuth

class User:

    def __init__(self, name, id_=None):
        """ Create new (volatile) user object

        :param name: str
        :param id_: str
        :return:
        """
        if id_ is None:
            id_ = gen_salt(40)
            while id in users:
                id = gen_salt(40)
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
    return users.get(session.get('user_id'))

def login_required(c):
    @wraps(c)
    def first_check(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for(
                'login',
                next=request.path))
        else:
            return c(*args, **kwargs)
    return first_check

def create_app():
    app = Flask(__name__)
    app.config.update({
        'DEBUG': True,
        'SECRET_KEY': 'lol-secret-key',
    })
    oauth = OAuth(app)
    consumer_key = ''
    consumer_secret = ''
    oauthhub = oauth.remote_app(
        'oauthhub',
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        request_token_params={
            'realm': 'read'},
        base_url='http://127.0.0.1:5000/api/v1/',
        request_token_url='http://127.0.0.1:5000/oauth/request-token',
        access_token_method='GET',
        access_token_url='http://127.0.0.1:5000/oauth/access-token',
        authorize_url='http://127.0.0.1:5000/oauth/authorize')
    oauthhub.tokengetter(get_access_token)

    @app.route('/')
    @login_required
    def index():
        current_user = get_current_user()
        return render_template(
            'user.html',
            user=current_user)

    @app.route('/login/')
    def login():
        return oauthhub.authorize(
            callback=url_for(
                'callback',
                next=request.args.get('next') or url_for('index'),
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
            user = User(user_resp.data['name'])
            save_user(user)
            log_user_in(user)
            return redirect(url_for('index'))

    @app.route('/logout/')
    def logout():
        log_user_out()
        return redirect(url_for('index'))

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port='5000')
