import unittest
import webapp2


class BaseTestCase(unittest.TestCase):

    def tearDown(self):
        # Clear thread-local variables.
        self.clear_globals()

    def clear_globals(self):
        webapp2._local.__release_local__()
