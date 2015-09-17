from flask import (abort, flash, redirect, render_template, request,
        url_for)

from login_status import login_required, get_current_user
from models import db, UserSPAccess
from error_handling import show_error_page

def add_ui_controllers_to_app(app, providers):
    @app.route('/')
    def index():
        return redirect(url_for('show_user'))

    @app.route('/user')
    @login_required
    def show_user():
        user = get_current_user()
        assert user is not None, "login_required didn't work??"
        if user.accesses_to_sps.count():
            authorised_services = user.accesses_to_sps.all()
            for service_record in authorised_services:
                service_name = service_record.sp_class_name
                if service_name in providers:
                    service = providers[service_name]
                    # TODO potentially remove the service if it's not valid.
                    if not app.config.get('DEBUG'):
                        if not service.verify():
                            continue
                        name = service.name()
                    else:
                        name = "(debug mode; saving get-name API call.)"
                    return render_template('user.html', name=name, providers=authorised_services)
        return show_error_page("Got into show_user with user set to None or no associations with service providers.")

    @app.route('/user/providers/remove/<provider_id>')
    @login_required
    def user_providers_remove(provider_id=None):
        if provider_id is None:
            return redirect(url_for('show_user'))
        user = get_current_user()
        assert user is not None, "login_required didn't work??"
        number_of_sps = user.accesses_to_sps.count()
        if number_of_sps == 0:
            flash("You have no accounts to remove.")
            return redirect(url_for('show_user'))
        elif number_of_sps == 1:
            flash("You cannot remove your last account.")
            return redirect(url_for('show_user'))
        else:
            provider = (user.accesses_to_sps
                .filter(UserSPAccess.id == provider_id)
                .one())
            db.session.delete(provider)
            db.session.commit()
            return redirect(url_for('show_user'))

    @app.route('/login/<service_provider>/')
    def login(service_provider):
        if service_provider in providers:
            return (providers[service_provider]
                    .client
                    .authorize(callback=url_for(
                            'oauth_authorized',
                            service_provider_name = service_provider,
                            next=request.args.get('next') or request.referrer or url_for('show_user'),
                            _external=True)))
        else:
            abort(404)

    @app.route('/login/')
    def login_options():
        next_url = request.args.get('next') or url_for('show_user')
        return render_template('login.html', next_url=next_url)
