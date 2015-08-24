#!/usr/bin/env python

import os
import unittest
from flask_oauthlib.client import OAuth

from models import db, User, UserSPAccess 
from service_provider import Twitter
import user_functions as uf

info = lambda *a, **k: None

class UserFunctionsTest(unittest.TestCase):
    def setUp(self):
        info("Create tables.")
        db.create_all()

    def test_add_user(self):
        uf.addUser(sp, 'test', 'test')
        
        self.assertEqual(1, len(User.query.all()))
        self.assertEqual(1, len(UserSPAccess.query.all()))

    def test_get_user(self):
        user_created = uf.addUser(sp, 'test', 'test')

        user_retrieved = uf.getUser(sp, 'test', 'test')
        
        self.assertEqual(user_created, user_retrieved)

    def test_get_or_add_user_existing_user(self):
        user_created = uf.addUser(sp, 'test', 'test')

        user_retrieved = uf.getOrCreateUser(sp, 'test', 'test')
        
        self.assertEqual(user_created, user_retrieved)

    def test_get_or_add_user_non_existing_user(self):
        user_retrieved = uf.getOrCreateUser(sp, 'test', 'test')
        
        self.assertEqual(1, len(User.query.all()))
        self.assertEqual(1, len(UserSPAccess.query.all()))

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
    app = db.get_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
    app = OAuth(app)
    sp = Twitter(app)
    unittest.main()
