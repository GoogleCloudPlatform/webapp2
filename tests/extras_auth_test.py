import webapp2
from webapp2_extras import sessions

from webapp2_extras import auth
from webapp2_extras.appengine.auth import models
from webapp2_extras.appengine.ndb import unique_model

import test_base

class TestAuth(test_base.BaseTestCase):

    def setUp(self):
        super(TestAuth, self).setUp()
        self.register_model('User', models.User)
        self.register_model('UserToken', models.UserToken)
        self.register_model('Unique', unique_model.Unique)

    def _check_token(self, auth_id, token, subject='auth'):
        rv = models.UserToken.get(user=auth_id, subject=subject, token=token)
        return rv is not None

    def test_get_user_by_password(self):
        app = webapp2.WSGIApplication(config={
            'webapp2_extras.sessions': {
                'secret_key': 'foo',
            }
        })
        req = webapp2.Request.blank('/')
        req.app = app
        s = auth.get_store(app=app)
        a = auth.get_auth(request=req)
        session_store = sessions.get_store(request=req)

        m = models.User
        success, user = m.create_user(name='name_1', username='username_1',
                                      auth_id='auth_id_1', email='email_1',
                                      password_raw='password')

        rv = a.get_user_by_password('auth_id_1', 'password')
        self.assertTrue(rv, s.user_to_dict(user))

    def test_validate_password(self):
        app = webapp2.WSGIApplication()
        req = webapp2.Request.blank('/')
        req.app = app
        s = auth.get_store(app=app)

        m = models.User
        success, user = m.create_user(name='name_1', username='username_1',
                                      auth_id='auth_id_1', email='email_1',
                                      password_raw='foo')

        u = s.validate_password('auth_id_1', 'foo')
        self.assertEqual(u, s.user_to_dict(user))
        self.assertRaises(auth.InvalidPasswordError,
                          s.validate_password, 'auth_id_1', 'bar')
        self.assertRaises(auth.InvalidAuthIdError,
                          s.validate_password, 'auth_id_2', 'foo')

    def test_validate_token(self):
        app = webapp2.WSGIApplication()
        req = webapp2.Request.blank('/')
        req.app = app
        s = auth.get_store(app=app)

        rv = s.validate_token('auth_id', 'token')
        self.assertEqual(rv, (None, None))

        # Expired timestamp.
        rv = s.validate_token('auth_id', 'token', -300)
        self.assertEqual(rv, (None, None))

        m = models.User
        success, user = m.create_user(name='name_1', username='username_1',
                                      auth_id='auth_id_1', email='email_1',
                                      password_raw='foo')

        token = m.create_auth_token('auth_id_1')
        rv = s.validate_token('auth_id_1', token)
        self.assertEqual(rv, (s.user_to_dict(user), token))
        # Token must still be there.
        self.assertTrue(self._check_token('auth_id_1', token))

        # Expired timestamp.
        token = m.create_auth_token('auth_id_1')
        rv = s.validate_token('auth_id_1', token, -300)
        self.assertEqual(rv, (None, None))
        # Token must have been deleted.
        self.assertFalse(self._check_token('auth_id_1', token))

        # Force expiration.
        token = m.create_auth_token('auth_id_1')
        s.config['token_max_age'] = -300
        rv = s.validate_token('auth_id_1', token)
        self.assertEqual(rv, (None, None))
        # Token must have been deleted.
        self.assertFalse(self._check_token('auth_id_1', token))

        # Revert expiration, force renewal.
        token = m.create_auth_token('auth_id_1')
        s.config['token_max_age'] = 86400 * 7 * 3
        s.config['token_new_age'] = -300
        rv = s.validate_token('auth_id_1', token)
        self.assertEqual(rv, (s.user_to_dict(user), None))
        # Token must have been deleted.
        self.assertFalse(self._check_token('auth_id_1', token))

    def test_set_auth_store(self):
        app = webapp2.WSGIApplication()
        req = webapp2.Request.blank('/')
        req.app = app
        store = auth.AuthStore(app)

        self.assertEqual(len(app.registry), 0)
        auth.set_store(store, app=app)
        self.assertEqual(len(app.registry), 1)
        s = auth.get_store(app=app)
        self.assertTrue(isinstance(s, auth.AuthStore))

    def test_get_auth_store(self):
        app = webapp2.WSGIApplication()
        req = webapp2.Request.blank('/')
        req.app = app
        self.assertEqual(len(app.registry), 0)
        s = auth.get_store(app=app)
        self.assertEqual(len(app.registry), 1)
        self.assertTrue(isinstance(s, auth.AuthStore))

    def test_set_auth(self):
        app = webapp2.WSGIApplication()
        req = webapp2.Request.blank('/')
        req.app = app
        a = auth.Auth(req)

        self.assertEqual(len(req.registry), 0)
        auth.set_auth(a, request=req)
        self.assertEqual(len(req.registry), 1)
        a = auth.get_auth(request=req)
        self.assertTrue(isinstance(a, auth.Auth))

    def test_get_auth(self):
        app = webapp2.WSGIApplication(config={
            'webapp2_extras.sessions': {
                'secret_key': 'my-super-secret',
            }
        })
        req = webapp2.Request.blank('/')
        req.app = app
        self.assertEqual(len(req.registry), 0)
        a = auth.get_auth(request=req)
        self.assertEqual(len(req.registry), 1)
        self.assertTrue(isinstance(a, auth.Auth))

    def test_set_callables(self):
        app = webapp2.WSGIApplication()
        req = webapp2.Request.blank('/')
        req.app = app
        s = auth.get_store(app=app)

        def validate_password(store, auth_id, password):
            self.assertTrue(store is s)
            self.assertEqual(auth_id, 'auth_id')
            self.assertEqual(password, 'password')
            return 'validate_password'

        def validate_token(store, auth_id, token, token_ts=None):
            self.assertTrue(store is s)
            self.assertEqual(auth_id, 'auth_id')
            self.assertEqual(token, 'token')
            self.assertEqual(token_ts, 'token_ts')
            return 'validate_token'

        s.set_password_validator(validate_password)
        rv = s.validate_password('auth_id', 'password')
        self.assertEqual(rv, 'validate_password')

        s.set_token_validator(validate_token)
        rv = s.validate_token('auth_id', 'token', 'token_ts')
        self.assertEqual(rv, 'validate_token')


if __name__ == '__main__':
    test_base.main()
