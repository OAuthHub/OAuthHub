from sqlalchemy.orm.exc import NoResultFound

from models import db, User, UserSPAccess


class UserNotFound(Exception):
    pass

def get_user(server, token, secret):
    try:
        user = User.query.join(UserSPAccess)\
            .filter(UserSPAccess.sp_class_name == server.get_service_name())\
            .filter(UserSPAccess.token == token)\
            .filter(UserSPAccess.secret == secret)\
            .one()
    except NoResultFound:
        raise UserNotFound()

    return user

def create_user():
    user = User()
    db.session.add(user)
    db.session.commit()
    return user

def add_SP_to_user(user, server, token, secret):
    access = create_SP_access(server, token, secret)
    user.accesses_to_sps.append(access)
    db.session.add(user)
    db.session.commit()

def add_SP_to_user_by_id(user_id, server, token, secret):
    user = get_user_by_id(user_id)
    add_SP_to_user(user, server,  token, secret)

def get_user_by_id(user_id):
    return User.query.filter(User.id == user_id).one()

def create_SP_access(service, token, secret):
    access = UserSPAccess(sp_class_name=service.get_service_name(), token=token, secret=secret)
    access.remote_user_id = service.get_id(token=(token, secret))
    db.session.add(access)
    db.session.commit()
    return access

def get_user_by_remote_id(provider, token=None):
    try:
        remote_id = provider.get_id(token=token)
        access = User.query.join(UserSPAccess)\
            .filter(UserSPAccess.sp_class_name == provider.get_service_name())\
            .filter(UserSPAccess.remote_user_id == remote_id)\
            .one()
    except NoResultFound:
        raise UserNotFound()
