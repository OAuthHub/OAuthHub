
"""
Flask-OAuthlib API specification tester

This file iterates the requirements that Flask-OAuthlib poses on the classes
which are used in the various hooks in the form of executable tests.

Use FlaskOAuthlibSpecs as a mixin for your unittest.TestCase subclasses.
"""

class FlaskOAuthlibSpecs:
    """
    Expected to be mixed in to a subclass of unittest.TestCase.
    """

    def _check_attr_of_type(self, obj, attr, type_):
        """ Check that: isinstance(obj.attr, type_)

        :param obj: object
        :param attr: str
        :param type_: type
        :return: None
        """
        self.assertTrue(hasattr(obj, attr), "obj: {!r}, attr: {}".format(
            obj, attr))
        self.assertTrue(isinstance(getattr(obj, attr), type_),
                "<obj: {!r}, attr: {!r}, obj.attr: {!r}, expected_type: {}>"
                    .format(obj, attr, getattr(obj, attr), type_))

    def _check_nonempty_container(self, box, box_type, elem_type):
        """ Check that box is a non-empty box-type of elem-type elements.

        :param tester: unittest.TestCase
        :param box: iterable
        :param box_type: container type
        :param elem_type: element type
        :return: None
        """
        self.assertTrue(isinstance(box, box_type))
        try:
            it = iter(box)
            n = next(it)
            self.assertIsInstance(n, elem_type)
        except StopIteration:
            self.fail("Container was empty.")

    def api_test_client(self, c):
        for attr in ['client_key', 'client_secret', 'default_redirect_uri']:
            self._check_attr_of_type(c, attr, str)
        for attr in ['redirect_uris', 'realms']:
            self._check_attr_of_type(c, attr, list)
            self._check_nonempty_container(getattr(c, attr), list, str)

    def api_test_request_token(self, rt, user_type, client_type):
        for attr in ['token', 'secret', 'redirect_uri', 'verifier']:
            self._check_attr_of_type(rt, attr, str)
        self._check_attr_of_type(rt, 'user', user_type)
        self._check_attr_of_type(rt, 'client', client_type)
        self._check_attr_of_type(rt, 'realms', list)
        self._check_nonempty_container(rt.realms, list, str)
        self._check_attr_of_type(rt, 'client_key', str)  # Undocumented!

    def api_test_nonce(self, n):
        for attr in ['client_key', 'nonce', 'request_token', 'access_token']:
            self._check_attr_of_type(n, attr, str)
        self._check_attr_of_type(n, 'timestamp', int)

    def api_test_access_token(self, at, user_type, client_type):
        for attr in ['token', 'secret']:
            self._check_attr_of_type(at, attr, str)
        self._check_attr_of_type(at, 'realms', list)
        self._check_nonempty_container(at.realms, list, str)
        self._check_attr_of_type(at, 'client', client_type)
        self._check_attr_of_type(at, 'user', user_type)
        self._check_attr_of_type(at, 'client_key', str)  # Undocumented!
