import logging
from models import db, User, AccessToken, OAuthServer
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

def getUser(db, server, token, secret):
    try:
        user = User.query.join(AccessToken)\
            .filter(AccessToken.server_id == server.id)\
            .filter(AccessToken.token == token)\
            .filter(AccessToken.secret == secret)\
            .one()
    except NoResultFound as nrf:
        logging.exception("Didn't find user")
        return None
    except MultipleResultsFound as mrf:
        logging.exception("Found too many users")
        raise

    return user

def addUser(db, server, token, secret):
    user = User()
    accessToken = AccessToken(server_id=server.id, token=token, secret=secret)
    user.authorizations.append(accessToken)
    db.session.add(user)
    db.session.commit()

    return user

def getOrCreateUser(db, consumer, token, secret):
    user = getUser(db, consumer, token, secret)

    if user is None:
        user = addUser(db, consumer, token, secret)

    return user
