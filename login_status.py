
from functools import wraps
from flask import session, url_for, request, redirect
from models import User

def login_required(controller):
    @wraps(controller)
    def attempt_log_in(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for(
                'login_options',
                next=request.path))
        else:
            return controller(*args, **kwargs)
    return attempt_log_in

def get_current_user():
    """ Get the currently logged-in user (else None)

    :return: User or None
    """
    return (User.query
            .filter(User.id == session.get('user_id'))
            .first())

def log_user_in(user):
    """ Mark a user as currently logged-in, for the session

    :param user: User
    :return: None
    """
    session['user_id'] = user.id

def log_user_out():
    if 'user_id' in session:
        del session['user_id']