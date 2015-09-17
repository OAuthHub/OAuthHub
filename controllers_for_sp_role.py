
from flask import request, redirect, url_for, render_template

from login_status import login_required

def add_sp_role_controllers_to_app(app, oauthhub_as_sp):
    """ Add (OAuth SP) endpoints to your app.

    :param app: flask.Flask
    :param oauthhub_as_sp: flask_oauthlib.provider.oauth1.OAuth1Provider
    """
    _add_for_human(app, oauthhub_as_sp)
    _add_for_api(app, oauthhub_as_sp)

def _add_for_human(app, oauthhub_as_sp):
    """ Define pages for manual management

    :param app:
    :param oauthhub_as_sp:
    :return:
    """

    @app.route('/developer/apps', methods=['GET', 'POST'])
    #login_required
    def developers_apps():
        if request.method == 'GET':
            return """(A list of Consumer apps created by you,
                and a form to create a new one.)"""
        elif request.method == 'POST':
            # Create a new Consumer app
            # Maybe flash message?
            return redirect(url_for('developers_apps'))
        else:
            assert False, request.method

    @app.route('/developer/apps/<app_id>')
    #login_required
    def developer_app_details(app_id):
        return """Some details about app with Consumer Key {!r}.""".format(app_id)

def _add_for_api(app, oauthhub_as_sp):
    """ Define the big-3 OAuth 1.0 endpoints

    :param app:
    :param oauthhub_as_sp:
    :return:
    """

    @app.route('/oauth/request-token')
    @oauthhub_as_sp.request_token_handler
    def request_token():
        return {}

    @app.route('/oauth/access-token')
    @oauthhub_as_sp.access_token_handler
    def access_token():
        return {}

    @app.route('/oauth/authorize', methods=['GET', 'POST'])
    @login_required
    @oauthhub_as_sp.authorize_handler
    def oauth_authorise():
        if request.method == 'GET':
            return render_template('authorize.html', service_name='XXX', permissions=['a', 'b'])
        elif request.method == 'POST':
            if request.form['authorized'] == 'Yes'
                return True
