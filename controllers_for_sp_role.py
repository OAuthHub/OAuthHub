
import logging

from flask import request, redirect, url_for, render_template, flash
from werkzeug.security import gen_salt

from login_status import login_required, login_not_really_required
from models import db, Consumer, ConsumerUserAccess, RequestToken
from login_status import get_current_user

log = logging.getLogger(__name__)

def add_sp_role_controllers_to_app(app, oauthhub_as_sp):
    """ Add (OAuth SP) endpoints to your app.

    :param app: flask.Flask
    :param oauthhub_as_sp: flask_oauthlib.provider.oauth1.OAuth1Provider
    """
    _add_for_admin(app, oauthhub_as_sp)
    _add_for_oauth(app, oauthhub_as_sp)
    app.config.update({
        'OAUTH1_PROVIDER_ENFORCE_SSL': False,
        'OAUTH1_PROVIDER_KEY_LENGTH': (10, 100),
        'OAUTH1_PROVIDER_REALMS': ['read'],
    })

def _add_for_admin(app, oauthhub_as_sp):
    """ Define pages for manual management

    :param app:
    :param oauthhub_as_sp:
    :return:
    """

    @app.route('/developer/apps', methods=['GET', 'POST'])
    @login_required
    def developers_apps():
        session_user = get_current_user()
        if request.method == 'GET':
            consumers = (Consumer.query
                .filter(Consumer.creator == session_user)
                .all())
            log.debug("Showing list of Consumers: {}".format(
                consumers))
            return render_template(
                'consumer_list.html',
                consumers=consumers,
                creator_repr=repr(session_user))
        elif request.method == 'POST':
            redirect_urls = [request.form['redirect-url']]
            realms = request.form['realms'].split(' ')
            fresh_consumer = Consumer(
                session_user,
                gen_salt(40),
                gen_salt(80),
                redirect_uris=redirect_urls,
                realms=realms)
            log.debug("Trying to create new Consumer: {!r}".format(
                fresh_consumer))
            try:
                db.session.add(fresh_consumer)
                db.session.commit()
                flash(
                    "You have created a new Consumer app.",
                    category='success')
                log.debug("Consumer creation success. "
                          "Now there are {} Consumers.".format(
                    Consumer.query.count()))
            except Exception:      # TODO: What Exception type?
                db.session.rollback()
                flash(
                    "Consumer app creation failed.",
                    category='fail')
            return redirect(url_for('developers_apps'))
        else:
            assert False, request.method

    @app.route('/developer/apps/<app_id>', methods=['GET', 'POST'])
    @login_required
    def developer_app_details(app_id):
        if request.method == 'GET':
            c = Consumer.query.get(app_id)
            return render_template(
                'consumer_details.html',
                consumer=c)
        elif request.method == 'POST':
            redirect_url = request.form['redirect-url']
            realms = request.form['realms']
            c = Consumer.query.get(app_id)
            c._redirect_uris = redirect_url
            c._realms = realms
            db.session.add(c)
            db.session.commit()
            return redirect(request.path)
        else:
            assert False, request.method

def _add_for_oauth(app, oauthhub_as_sp):
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
    @login_not_really_required
    @oauthhub_as_sp.authorize_handler
    def oauth_authorise(*args, **kwargs):
        if request.method == 'GET':
            log.debug("oauth_authorise was called.")
            log.debug("args: {!r}".format(args))
            log.debug("kwargs: {!r}".format(kwargs))
            # Don't know why, but args always passed in as kwargs.
            realms = kwargs['realms']
            request_token = kwargs['resource_owner_key']
            # Anyway.
            assert isinstance(realms, list), repr(realms)
            assert realms, realms
            assert isinstance(realms[0], str), repr(realms[0])
            assert isinstance(request_token, str), repr(request_token)
            log.debug("The above args/kwargs are interpretted as:")
            log.debug("Realms: {!r}".format(realms))
            log.debug("Request token: {!r}".format(request_token))
            request_token = (RequestToken.query
                .filter_by(token=request_token)
                .one())
            return render_template(
                'authorize.html',
                consumer=request_token.client,
                permissions=realms)
        elif request.method == 'POST':
            return request.form['authorized'] == 'yes'
