#!/usr/bin/env python

import os
import unittest
from models import db, Consumer, ConsumerUserAccess

info = lambda *a, **k: None

class ModelsTest(unittest.TestCase):

    def setUp(self):
        info("Create tables.")
        db.create_all()
        self.assertEqual([], Consumer.query.all())
        self.assertEqual([], ConsumerUserAccess.query.all())
        info("Tables created.")

        # Test insert; also sets up for other tests.
        c = Consumer(key='my-key', secret='my-secret')
        self.assertEqual([], Consumer.query.all())
        db.session.add(c)
        self.assertEqual([c], Consumer.query.all())  # Volatile!
        db.session.commit() 
        self.assertEqual([c], Consumer.query.all())  # Persisted.

    def test_select(self):
        consumers = Consumer.query.all()
        self.assertEqual(1, len(consumers))
        c = consumers[0]
        self.assertEqual('my-key', c.key)
        self.assertEqual('my-secret', c.secret)

    def test_update(self):
        c = Consumer.query.one()
        c.key = 'new-key'
        another_ref = Consumer.query.one()
        self.assertEqual('new-key', another_ref.key)  # Volatile?
        db.session.commit()  # Persisted.

    def test_delete(self):
        c = Consumer.query.one()
        db.session.delete(c)
        self.assertEqual([], Consumer.query.all())  # Volatile?
        db.session.commit()
        self.assertEqual([], Consumer.query.all())  # Persisted.

    def tearDown(self):
        info("Drop tables.")

        # Otherwise hangs at drop_all.
        # More info: http://stackoverflow.com/questions/24289808/drop-all-freezes-in-flask-with-sqlalchemy
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
    unittest.main()
