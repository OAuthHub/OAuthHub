class ResourceNotAvailable(RuntimeError):
    pass

class ServiceProviderDict(dict):
    def add_provider(self, service_provider):
        try:
            key = service_provider._get_service_name()
        except AttributeError as ae:
            raise TypeError("You must implement _get_service_name().")

        self[key] = service_provider

class ServiceProvider():
    def __init__(self, app):
        self._client = _build_client(app)
        self._client.tokengetter(self._get_token)

    def _get_token(self, token=None):
        user_id = session.get('user_id')

        latestToken = UserSPAccess.query\
            .filter(UserSPAccess.user_id == user_id)\
            .filter(UserSPAccess.sp_class_name == self._get_service_name())\
            .order_by(db.desc(UserSPAccess.id))\
            .first()

        if latestToken is None:
            return None

        return (latestToken.token, latestToken.secret)

    def _build_client(self, app):
        """ Should return an instance of a an oauth remote app. """
        raise NotImplementedError()

    def _get_service_name(self):
        raise NotImplementedError()

    def verify(self):
        """ Check that this connection is valid. """
        raise NotImplementedError()

    def name(self):
        """ This is an example of how a resource would be defined for an SP. """
        raise NotImplementedError()

class Twitter(ServiceProvider):
    def _build_client(self, app):
        return app.remote_app('twitter',
            base_url='https://api.twitter.com/1.1/',
            request_token_url='https://api.twitter.com/oauth/request_token',
            access_token_url='https://api.twitter.com/oauth/access_token',
            authorize_url='https://api.twitter.com/oauth/authenticate',
            consumer_key=os.environ['TWITTER_CONSUMER_KEY'],
            consumer_secret=os.environ['TWITTER_SECRET_KEY']
        )

    def _get_service_name(self):
        return 'twitter'

    def verify(self):
        """ Check that this connection is valid. """
        resp = self._client.get('account/verify_credentials.json')

        if resp.status == 200:
            return True

        return False

    def name(self):
        """ This is an example of how a resource would be defined for an SP. """

        resp = self.client.get('account/verify_credentials.json')

        if not resp.status == 200:
            raise ResourceNotAvailable("Server responded with {}. Message: {}".format(resp.status, resp.raw_data))

        try:
            return resp.data['name']
        except KeyError as ke:
            raise ResourceNotAvailable("Server did not send the name")
