
from functools import wraps
from flask import session, url_for, request, redirect
from sqlalchemy.orm.exc import NoResultFound
from models import User

def login_required(function):
    @wraps(function)
    def attempt_log_in(*args, **kwargs):
        try:
            user = User.query.filter(User.id == session.get('user_id')).one()
        except NoResultFound:
            return redirect('/login/?next=/user')

        kwargs['user'] = user

        return function(*args, **kwargs)

    return attempt_log_in

def currently_logged_in():
    return 'user_id' in session

def current_user_id():
    return session['user_id']

def log_user_in(user):
    session['user_id'] = user.id