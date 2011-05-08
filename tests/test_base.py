import unittest

from google.appengine.ext import testbed


def main():
    unittest.main()


class BaseTestCase(unittest.TestCase):
    DEFAULT_APP_ID = testbed.DEFAULT_APP_ID
    DEFAULT_AUTH_DOMAIN = testbed.DEFAULT_AUTH_DOMAIN
    DEFAULT_SERVER_SOFTWARE = testbed.DEFAULT_SERVER_SOFTWARE
    DEFAULT_SERVER_NAME = testbed.DEFAULT_SERVER_NAME
    DEFAULT_SERVER_PORT = testbed.DEFAULT_SERVER_PORT

    def setUp(self):
        """Set up the test framework.

        Service stubs are available for the following services:

        - Datastore (use init_datastore_v3_stub)
        - Memcache (use init_memcache_stub)
        - Task Queue (use init_taskqueue_stub)
        - Images (only for dev_appserver; use init_images_stub)
        - URL fetch (use init_urlfetch_stub)
        - User service (use init_user_stub)
        - XMPP (use init_xmpp_stub)
        """
        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()

        # Bug in testbed: even if you call setup_env() before activate(),
        # setup_env() is called again using default values. So we wrap it.
        self._orig_setup_env = self.testbed.setup_env
        self.testbed.setup_env = self.setup_env

        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()

        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()

        # Only when testing ndb.
        self.setup_context_cache()

    def tearDown(self):
        # This restores the original stubs so that tests do not interfere
        # with each other.
        self.testbed.deactivate()
        self.testbed.setup_env = self._orig_setup_env

    def setup_env(self, **kwargs):
        kwargs.setdefault('app_id', self.DEFAULT_APP_ID)
        kwargs.setdefault('auth_domain', self.DEFAULT_AUTH_DOMAIN)
        kwargs.setdefault('server_software', self.DEFAULT_SERVER_SOFTWARE)
        kwargs.setdefault('server_name', self.DEFAULT_SERVER_NAME)
        kwargs.setdefault('server_port', self.DEFAULT_SERVER_PORT)

        self._orig_setup_env(**kwargs)

    def setup_context_cache(self):
        """Set up the context cache.

        We only need cache active when testing the cache, so the default
        behavior is to disable it to avoid misleading test results. Override
        this when needed.
        """
        from ndb import tasklets
        ctx = tasklets.get_context()
        ctx.set_cache_policy(lambda key: False)
        ctx.set_memcache_policy(lambda key: False)
