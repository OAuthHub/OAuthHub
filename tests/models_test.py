#!/usr/bin/env python

import os
import unittest
import logging
import subprocess

from tests.flask_oauthlib_api_spec import FlaskOAuthlibSpecs
from models import (db, Consumer, ConsumerUserAccess, User,
        RequestToken, AccessToken, Nonce)

log = logging.getLogger(__name__)

CONSUMER_KEY = '123456789012345678901234567890'
CONSUMER_SECRET = '1234567890123456789012345678901234567890'
REQUEST_TOKEN = '123456789012345678901234567890'
REQUEST_TOKEN_SECRET = '1234567890123456789012345678901234567890'
ACCESS_TOKEN = '123456789012345678901234567890'
ACCESS_TOKEN_SECRET = '1234567890123456789012345678901234567890'
TIMESTAMP = 1442305580
NONCE = '1234567890123456789012345678901234567890'
REALM = 'read'
USERNAME = "Mike O'Sullivan"
REDIRECT_URI = 'http://localhost:8000/callback'

class ModelsTest(unittest.TestCase):

    def setUp(self):
        log.debug("Create tables.")
        db.create_all()
        self.assertEqual([], Consumer.query.all())
        self.assertEqual([], ConsumerUserAccess.query.all())
        log.debug("Tables created.")

        # Test insert; also sets up for other tests.
        u = User(name="Mike O'Sullivan")
        c = Consumer(
            creator=u,
            client_key='my-key',
            client_secret='my-secret',
            redirect_uris=['http://localhost:8000/callback'],
            realms=['read'])
        self.assertEqual([], Consumer.query.all())
        db.session.add(u)
        db.session.add(c)
        self.assertEqual([c], Consumer.query.all())  # Volatile!
        db.session.commit()
        self.assertEqual([c], Consumer.query.all())  # Persisted.

    def test_select(self):
        consumers = Consumer.query.all()
        self.assertEqual(1, len(consumers))
        c = consumers[0]
        self.assertEqual('my-key', c.client_key)
        self.assertEqual('my-secret', c.client_secret)

    def test_update(self):
        c = Consumer.query.one()
        c.client_key = 'new-key'
        another_ref = Consumer.query.one()
        self.assertEqual('new-key', another_ref.client_key)  # Volatile?
        db.session.commit()  # Persisted.

    def test_delete(self):
        c = Consumer.query.one()
        db.session.delete(c)
        self.assertEqual([], Consumer.query.all())  # Volatile?
        db.session.commit()
        self.assertEqual([], Consumer.query.all())  # Persisted.

    def test_relationships(self):
        cua = ConsumerUserAccess(token='CU-AT', secret='CU-ATS')
        # C
        c = Consumer.query.one()
        cua.consumer = c
        self.assertEqual([cua], c.accesses_to_users.all())
        # U
        u = User.query.one()
        self.assertTrue(u.name.startswith("Mike"))
        cua.user = u
        self.assertEqual([cua], u.accesses_from_consumers.all())
        # Persist
        db.session.add(cua)
        db.session.commit()
        self.assertEqual([cua], Consumer.query.one().accesses_to_users.all())
        self.assertEqual([cua], User.query.one().accesses_from_consumers.all())

    def tearDown(self):
        log.debug("Drop tables.")

        # Otherwise hangs at drop_all.
        # More info: http://stackoverflow.com/questions/24289808/
        db.session.commit()

        db.drop_all()
        log.debug("Tables dropped.")

class FlaskOAuthlibModelsSpecTest(unittest.TestCase, FlaskOAuthlibSpecs):

    def setUp(self):
        self.user = User(name=USERNAME)
        self.consumer = Consumer(
            creator=self.user,
            client_key=CONSUMER_KEY, # 30 chars
            client_secret=CONSUMER_SECRET,
            redirect_uris=[REDIRECT_URI],
            realms=[REALM])
        self.request_token = RequestToken(
            client=self.consumer,
            token=REQUEST_TOKEN,
            secret=REQUEST_TOKEN_SECRET,
            realms=[REALM],
            redirect_uri=REDIRECT_URI,
            user=self.user)
        self.nonce = Nonce(
            client_key=CONSUMER_KEY,
            timestamp=TIMESTAMP,
            nonce=NONCE,
            request_token=REQUEST_TOKEN,
            access_token=ACCESS_TOKEN)
        self.access_token = AccessToken(
            client=self.consumer,
            user=self.user,
            realms=[REALM],
            token=ACCESS_TOKEN,
            secret=ACCESS_TOKEN_SECRET)

    def test_types(self):
        self.api_test_client(self.consumer)
        self.api_test_request_token(self.request_token, User, Consumer)
        self.api_test_access_token(self.access_token, User, Consumer)
        self.api_test_nonce(self.nonce)

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
    unittest.main()
