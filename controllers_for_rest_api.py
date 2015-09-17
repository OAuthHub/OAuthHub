

""" Implements OAuthHub REST API

Documentation spec:

https://docs.google.com/document/d/1sWBUsX-DUhBvi94Aja9iVpikKC_khXxkNRAIArReCVM/edit#
"""

from flask import jsonify, request

from models import User

_API_BASE_PATH = '/api/v1'

def add_rest_api_controllers_to_app(app, provider):
    """ Add more endpoints to your app

    :param app: flask.Flask
    :param provider: flask_oauthlib.provider.oauth1.OAuth1Provider
    :return: None
    """

    @app.route(_API_BASE_PATH + '/user.json')
    @provider.require_oauth('read')
    def user():
        user = request.oauth.user
        assert isinstance(user, User), "user: {!r}, of type {}".format(
            user, type(user))
        return jsonify(
            id=user.id,
            name=user.name)
