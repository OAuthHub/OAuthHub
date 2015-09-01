import logging

from flask import session, url_for
from functools import wraps
from models import db, User, UserSPAccess
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

def getUser(server, token, secret):
    try:
        user = User.query.join(UserSPAccess)\
            .filter(UserSPAccess.sp_class_name == server.get_service_name())\
            .filter(UserSPAccess.token == token)\
            .filter(UserSPAccess.secret == secret)\
            .one()
    except NoResultFound:
        logging.exception("Didn't find user")
        return None
    except MultipleResultsFound:
        logging.exception("Found too many users")
        raise

    return user

def addUser(server, token, secret):
    user = User()
    db.session.add(user)
    db.session.commit()

    add_SP_to_user(user, server, token, secret)

    return user

def getOrCreateUser(server, token, secret):
    user = getUser(server, token, secret)

    if user is None:
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
        except MultipleResultsFound:
            raise

        kwargs['user'] = user

        return function(*args, **kwargs)

    return attempt_log_in

def add_SP_to_user(user, server, token, secret):
    access = UserSPAccess(sp_class_name=server.get_service_name(), token=token, secret=secret)
    user.accesses_to_sps.append(access)
    db.session.add(user)
    db.session.commit()
