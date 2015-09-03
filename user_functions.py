import logging

from flask import session, url_for
from functools import wraps
from models import db, User, UserSPAccess
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

class UserNotFound(Exception):
    pass

def getUser(server, token, secret):
    try:
        user = User.query.join(UserSPAccess)\
            .filter(UserSPAccess.sp_class_name == server.get_service_name())\
            .filter(UserSPAccess.token == token)\
            .filter(UserSPAccess.secret == secret)\
            .one()
    except NoResultFound:
        raise UserNotFound()

    return user

def addUser(server, token, secret):
    user = User()
    db.session.add(user)
    db.session.commit()

    add_SP_to_user(user, server, token, secret)

    return user

def getOrCreateUser(server, token, secret):
    try:
        user = getUser(server, token, secret)
    except UserNotFound:
        user = addUser(server, token, secret)

    return user

def login_required(function):
    @wraps(function)
    def attempt_log_in(*args, **kwargs):
        try:
            user = User.query.filter(User.id == session.get('user_id')).one()
        except NoResultFound:
            #return redirect(url_for(not_logged_in))
            return 'You aren\'t logged in! <a href="' + url_for('login', service_provider='twitter') + '">login</a>'

        kwargs['user'] = user

        return function(*args, **kwargs)

    return attempt_log_in

def add_SP_to_user(user, server, token, secret):
    access = UserSPAccess(sp_class_name=server.get_service_name(), token=token, secret=secret)
    user.accesses_to_sps.append(access)
    db.session.add(user)
    db.session.commit()

def add_SP_to_user_by_id(user_id, server, token, secret):
    user = get_user_by_id(user_id)
    add_SP_to_user(user, current_provider,  token, secret)

def get_user_by_id(user_id):
    return User.query.filter(User.id == user_id).one()

def currently_logged_in():
    return 'user_id' in session

def current_user_id():
    return session['user_id']

def log_user_in(user):
    session['user_id'] = user.id
