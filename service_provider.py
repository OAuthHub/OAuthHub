from os import environ
from flask import session
import requests
from requests.auth import HTTPBasicAuth

from models import db, UserSPAccess
from error_handling import ServiceProviderNotFound, UserDeniedRequest


class ResourceNotAvailable(RuntimeError):
    pass

class ServiceProviderDict(dict):

    def add_provider(self, service_provider):
        try:
            key = service_provider.get_service_name()
        except AttributeError as ae:
            raise TypeError("You must implement get_service_name().")
        self[key] = service_provider

    def get_by_name(self, name):
        try:
            return self[name]
        except KeyError:
            raise ServiceProviderNotFound("No SP of name: {}".format(name))

def _extract_tokens(resp):
    token = None
    secret = None
    if 'oauth_token' in resp: # OAuth1
        token = resp['oauth_token']
        secret = resp['oauth_token_secret']
    elif 'access_token' in resp: # OAuth2
        token = resp['access_token']
    return (token, secret)


class ServiceProvider():
    def __init__(self, oauth):
        self.client = self._build_client(oauth)
        self.client.tokengetter(self._get_token)

    def _get_token(self, token=None):
        if token is not None:
            return token

        user_id = session.get('user_id')

        latestToken = UserSPAccess.query\
            .filter(UserSPAccess.user_id == user_id)\
            .filter(UserSPAccess.sp_class_name == self.get_service_name())\
            .order_by(db.desc(UserSPAccess.id))\
            .first()

        if latestToken is None:
            return None

        return (latestToken.token, latestToken.secret)

    def _build_client(self, oauth):
        """ Should return an instance of a an oauth remote app. """
        raise NotImplementedError()

    def get_service_name(self):
        return self.client.name

    def verify(self, token=None):
        """ Check that this connection is valid. """
        raise NotImplementedError()

    def name(self, token=None):
        """ This is an example of how a resource would be defined for an SP. """
        raise NotImplementedError()

    def get_id(self, token=None):
        raise NotImplementedError()

    def get_access_tokens(self):
        """ Return a pair of strings, the second of which is None for OAuth 2.

        :return: (access_token, access_token_secret)
        """
        resp = self.client.authorized_response()
        if resp is None:
            raise UserDeniedRequest()
        else:
            return _extract_tokens(resp)

class Twitter(ServiceProvider):
    def _build_client(self, oauth):
        return oauth.remote_app('twitter',
            base_url='https://api.twitter.com/1.1/',
            request_token_url='https://api.twitter.com/oauth/request_token',
            access_token_url='https://api.twitter.com/oauth/access_token',
            authorize_url='https://api.twitter.com/oauth/authenticate',
            consumer_key=environ['TWITTER_CONSUMER_KEY'],
            consumer_secret=environ['TWITTER_CONSUMER_SECRET']
        )

    def _get_credential_field(self, field_name, token=None):
        resp = self.client.request('account/verify_credentials.json', token=token, method='GET')

        if not resp.status == 200:
            raise ResourceNotAvailable("Server responded with {}. Message: {}".format(resp.status, resp.raw_data))

        try:
            return resp.data[field_name]
        except KeyError as ke:
            raise ResourceNotAvailable("Server did not send the {}".format(field_name))

    def verify(self, token=None):
        """ Check that this connection is valid. """
        resp = self.client.get('account/verify_credentials.json', token=token)

        return resp.status == 200

    def name(self, token=None):
        return self._get_credential_field('name', token)

    def get_id(self, token=None):
        return self._get_credential_field('id', token)

class GitHub(ServiceProvider):
    def _build_client(self, oauth):
        return oauth.remote_app('github',
            consumer_key='6bcf6d2df5ff0f003735',
            consumer_secret='ebb3d95e13d0a87cdd9614ede2f9b87a16e87fd9',
            request_token_params={'scope': 'user'},
            base_url='https://api.github.com/',
            request_token_url=None,
            access_token_method='POST',
            access_token_url='https://github.com/login/oauth/access_token',
            authorize_url='https://github.com/login/oauth/authorize'
        )

    def _get_credential_field(self, field_name, token=None):
        resp = self.client.get('user', token=token, method='GET')

        if not resp.status == 200:
            raise ResourceNotAvailable("Server responded with {}. Message: {}".format(resp.status, resp.raw_data))

        try:
            return resp.data[field_name]
        except KeyError as ke:
            raise ResourceNotAvailable("Server did not send the {}".format(field_name))

    def verify(self, token=None):
        url = '{base_url}applications/{client_id}/tokens/{access_token}'.format(
            base_url=self.client._base_url,
            client_id=self.client._consumer_key,
            access_token=self.client._tokengetter(token=token)[0])
        response = requests.get(url, auth=HTTPBasicAuth(self.client._consumer_key, self.client._consumer_secret))

        return response.status_code == 200

    def name(self, token=None):
        return self._get_credential_field('name', token)

    def get_id(self, token=None):
        return self._get_credential_field('id', token)
