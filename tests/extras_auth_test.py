from experimental import auth
from experimental.appengine.auth import models
from experimental.appengine.ndb import unique_model

import test_base

class TestAuth(test_base.BaseTestCase):

    def setUp(self):
        super(TestAuth, self).setUp()
        self.register_model('User', models.User)
        self.register_model('UserToken', models.UserToken)
        self.register_model('Unique', unique_model.Unique)


if __name__ == '__main__':
    test_base.main()
