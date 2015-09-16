#!/usr/bin/env python

import os
import unittest
from flask_oauthlib.client import OAuth

from models import db, User, UserSPAccess, create_app
from service_provider import ServiceProvider
import user_functions as uf

info = lambda *a, **k: None

class MockRemoteApplication():
    def tokengetter(self, f):
        return f

class MockServiceProvider(ServiceProvider):
    def _build_client(self, oauth):
        """ Should return an instance of a an oauth remote app. """
        return MockRemoteApplication()

    def get_service_name(self):
        return "MockService"

    def verify(self, token=None):
        """ Check that this connection is valid. """
        return True

    def name(self, token=None):
        """ This is an example of how a resource would be defined for an SP. """
        return "John Doe"

    def get_id(self, token=None):
        return "42"

class UserFunctionsTest(unittest.TestCase):
    def setUp(self):
        info("Create tables.")
        db.create_all()

    def test_add_user(self):
        uf.create_user()
        
        self.assertEqual(1, User.query.count())
        self.assertEqual(0, UserSPAccess.query.count())

    def test_get_user_by_tokens(self):
        user_created = uf.create_user()
        uf.add_SP_to_user(user_created, sp, 'test', 'test')

        user_retrieved = uf.get_user_by_token(sp, 'test', 'test')
        self.assertEqual(user_created, user_retrieved)

    def test_add_sp_to_user(self):
        user_created = uf.create_user()
        self.assertEqual(0, UserSPAccess.query.count())

        uf.add_SP_to_user(user_created, sp, 'test', 'test')
        self.assertEqual(1, UserSPAccess.query.count())

    def test_add_sp_to_user_by_id(self):
        user_created = uf.create_user()
        uf.add_SP_to_user_by_id(user_created.id, sp, 'test', 'test')

        self.assertEqual(1, UserSPAccess.query.count())
        self.assertEqual(1, User.query.join(UserSPAccess).count())

    def tearDown(self):
        info("Drop tables.")

        # Otherwise hangs at drop_all.
        # More info: http://stackoverflow.com/questions/24289808/
        db.session.commit()

        db.drop_all()
        info("Tables dropped.")

if __name__ == '__main__':
    uri = os.getenv('SQLALCHEMY_TESTING_DATABASE_URI')
    print('=' * 80)
    print('  WARNING: You may be about to drop your production database!')
    print('  Database URI in use for testing: {}'.format(uri))
    print('=' * 80)
    try:
        input('Press ^C to cancel, or <Enter> to continue')
    except KeyboardInterrupt:
        os.exit()

    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = uri

    sp = MockServiceProvider(None)

    with app.app_context():
        unittest.main()
