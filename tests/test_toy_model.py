import os
import subprocess
import logging
import unittest

from tests.toy_models import Product, Shelf, db, SQLITE_DB_FILENAME

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)

class TestToys(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.create_all()

    def setUp(self):
        p = Product('product-1')
        s = Shelf('shelf-1')
        p.shelf = s
        db.session.add(p)
        db.session.add(s)
        db.session.commit()

    def test_relationship(self):
        s = Shelf.query.first()
        self.assertEqual(1, s.products.count())
        p = Product.query.first()
        self.assertIs(p.shelf, s)

    @classmethod
    def tearDownClass(cls):
        db.session.commit()
        db.drop_all()
        path = os.path.join(
                os.path.dirname(__file__),
                SQLITE_DB_FILENAME.split('/')[-1])
        log.info("About to rm the file at: {}".format(path))
        o = (subprocess.check_output(['rm', '-fv', path])
                 .decode('utf-8')
                 .strip('\n'))
        log.info(o)

if __name__ == '__main__':
    unittest.main()
