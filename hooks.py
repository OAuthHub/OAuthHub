
import logging

from login_status import get_current_user
from models import (db, Consumer, ConsumerUserAccess, User, UserSPAccess,
        RequestToken, Nonce)

log = logging.getLogger(__name__)

def _load_client(client_key):
    return Consumer.query.filter(
        Consumer.client_key == client_key).first()

def _load_request_token(token):
    return RequestToken.query.filter(
        RequestToken.token == token).first()

def _save_request_token(token, req):
    rt = token['oauth_token']
    rts = token['oauth_token_secret']
    c = req.client
    log.debug("req.client: {!r}".format(c))
    uri = req.redirect_uri
    log.debug("req.redirect_uri: {!r}".format(uri))
    t = RequestToken(
        client=c,
        token=rt,
        secret=rts,
        redirect_uri=uri,
        realms=c.default_realms)
    db.session.add(t)
    db.session.commit()

def _load_verifier(verifier, token):
    return RequestToken.query.filter(
        RequestToken.verifier == verifier and
        RequestToken.token == token).first()

def _save_verifier(token, verifier):     # And args, kwargs
    t = RequestToken.query.filter(
        RequestToken.token == token).one()
    t.verifier = verifier
    t.user = get_current_user()
    db.session.add(t)
    db.session.commit()

def _load_access_token(client_key, token):   # And args, kwargs
    return ConsumerUserAccess.query.filter(
        ConsumerUserAccess.client_key == client_key and
        ConsumerUserAccess.token == token).first()

def _save_access_token(token, req):
    c = req.client
    u = req.user
    at = token['oauth_token']
    ats = token['oauth_token_secret']
    raw_realms = token['oauth_authorised_realms']
    realms = raw_realms.split(' ')
    assert all((
        isinstance(c, Consumer),
        isinstance(u, User),
        isinstance(at, str),
        isinstance(ats, str),
        isinstance(raw_realms, str),
        isinstance(realms, list))), repr((c, u, at, ats, raw_realms, realms))
    t = ConsumerUserAccess(
        client=c,
        user=u,
        realms=realms,
        token=at,
        secret=ats)
    db.session.add(t)
    db.session.commit()

def _load_nonce(client_key, timestamp, nonce, request_token, access_token):
    #http://docs.sqlalchemy.org/en/rel_1_0/orm/query.html#sqlalchemy.orm.query.Query.filter_by
    return (Nonce.query
            .filter_by(
                client_key=client_key,
                timestamp=timestamp,
                nonce=nonce,
                request_token=request_token,
                access_token=access_token)
            .first())

def _save_nonce(client_key, timestamp, nonce, request_token, access_token):
    n = Nonce(
        client_key=client_key,
        timestamp=timestamp,
        nonce=nonce,
        request_token=request_token,
        access_token=access_token)
    db.session.add(n)
    db.session.commit()

def register_all_hooks(provider):
    """ Register all hooks onto given provider

    :param provider: flask_oauthlib.provider.oauth1.OAuth1Provider
    :return: None
    """
    provider.clientgetter(_load_client)
    provider.tokengetter(_load_access_token)
    provider.tokensetter(_save_access_token)
    provider.grantgetter(_load_request_token)
    provider.grantsetter(_save_request_token)
    provider.noncegetter(_load_nonce)
    provider.noncesetter(_save_nonce)
    provider.verifiergetter(_load_verifier)
    provider.verifiersetter(_save_verifier)
