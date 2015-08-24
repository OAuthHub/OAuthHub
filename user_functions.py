import logging

from models import db, User, UserSPAccess
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

def getUser(server, token, secret):
    try:
        user = User.query.join(UserSPAccess)\
            .filter(UserSPAccess.sp_class_name == server.get_service_name())\
            .filter(UserSPAccess.token == token)\
            .filter(UserSPAccess.secret == secret)\
            .one()
    except NoResultFound as nrf:
        logging.exception("Didn't find user")
        return None
    except MultipleResultsFound as mrf:
        logging.exception("Found too many users")
        raise

    return user

def addUser(server, token, secret):
    user = User()
    access = UserSPAccess(sp_class_name=server.get_service_name(), token=token, secret=secret)
    user.accesses_to_sps.append(access)
    db.session.add(user)
    db.session.commit()

    return user

def getOrCreateUser(server, token, secret):
    user = getUser(server, token, secret)

    if user is None:
        user = addUser(server, token, secret)

    return user
