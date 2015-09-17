
import random
from functools import wraps

from flask import session, url_for, request, redirect
from werkzeug.security import gen_salt

from models import db, User

def login_required(controller):
    @wraps(controller)
    def attempt_log_in(*args, **kwargs):
        if not get_current_user():
            return redirect(url_for(
                'login_options',
                next=request.full_path))
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

def login_not_really_required(controller):
    """ Creates new user automatically if not existing in session

    :param controller:
    :return:
    """
    adverbs = ['Slightly', 'Very']
    adjectives = ['Red', 'Small', 'Vigorous', 'Sleepy']
    nouns = ['Elephant', 'Turkey', 'Snake', 'Cat']
    def gen_random_name():
        return ' '.join((
            random.choice(adverbs),
            random.choice(adjectives),
            random.choice(nouns)))

    @wraps(controller)
    def attempt_log_in(*args, **kwargs):
        if not get_current_user():
            fresh_user = User(name=gen_random_name())
            db.session.add(fresh_user)
            db.session.commit()
            log_user_in(fresh_user)
        return controller(*args, **kwargs)
    return attempt_log_in

