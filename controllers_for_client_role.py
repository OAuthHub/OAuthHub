from flask import flash, redirect, url_for, request

from login_status import get_current_user, log_user_in
from user_functions import (add_SP_to_user_by_id, create_user,
                            get_user_by_token, UserNotFound, get_user_by_remote_id)
from error_handling import ServiceProviderNotFound, UserDeniedRequest

def add_client_role_controllers_to_app(app, providers):

    # TODO: change URL to "/oauth/authorized" --- or better yet, "/oauth/callback"
    @app.route('/oauth-authorized/<service_provider_name>/')
    def oauth_authorized(service_provider_name):
        session_user = get_current_user()
        try:
            current_provider = providers.get_by_name(service_provider_name)
            token, secret = current_provider.get_access_tokens()
            fresh_user = get_user_by_token(current_provider, token, secret)
            if session_user is not None:
                if fresh_user.id == session_user.id:
                    flash('This provider was already linked to this account.')
                else:
                    flash('Merging accounts is not currently supported.')
            else:
                log_user_in(fresh_user)
        except ServiceProviderNotFound:
            flash('Provider not found.')
        except UserDeniedRequest:
            flash('You denied us access.')
        except UserNotFound:
            if session_user is None:
                try:
                    user = get_user_by_remote_id(current_provider, token=(token,secret))
                except UserNotFound:
                    user = create_user()
                log_user_in(user)
            add_SP_to_user_by_id(
                get_current_user().id, current_provider, token, secret)
        next_url = request.args.get('next') or url_for('show_user')
        return redirect(next_url)
