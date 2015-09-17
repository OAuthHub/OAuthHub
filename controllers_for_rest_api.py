

""" Implements OAuthHub REST API

Documentation spec:

https://docs.google.com/document/d/1sWBUsX-DUhBvi94Aja9iVpikKC_khXxkNRAIArReCVM/edit#
"""

from flask import jsonify, request

from models import User

_API_BASE_PATH = '/api/v1'


def get_users_name(user, providers):
    #TODO return something when the count is zero
    if user.accesses_to_sps.count():
        authorised_services = user.accesses_to_sps.all()
        for service_record in authorised_services:
            service_name = service_record.sp_class_name
            token = (service_record.token, service_record.secret)

            if service_name in providers:
                service = providers[service_name]

                if not service.verify(token=token):
                    continue

                return service.name(token=token)

def add_rest_api_controllers_to_app(app, provider, service_providers):
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
            name=get_users_name(user, service_providers))
