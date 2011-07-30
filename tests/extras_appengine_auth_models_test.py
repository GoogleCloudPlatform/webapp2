from webapp2_extras import auth
from webapp2_extras.appengine.auth import models
from webapp2_extras.appengine.ndb import unique_model

import test_base


class TestAuthModels(test_base.BaseTestCase):

    def setUp(self):
        super(TestAuthModels, self).setUp()
        self.register_model('User', models.User)
        self.register_model('UserToken', models.UserToken)
        self.register_model('Unique', unique_model.Unique)

    def test_get(self):
        m = models.User
        success, user = m.create_user(auth_id='auth_id_1', password_raw='foo')
        self.assertEqual(success, True)
        self.assertTrue(user is not None)
        self.assertTrue(user.password is not None)

        # user.key.id() is required to retrieve the auth token
        user_id = user.key.id()

        token = m.create_auth_token(user_id)

        self.assertEqual(m.get_by_auth_id('auth_id_1'), user)
        self.assertEqual(m.get_by_auth_id('auth_id_2'), None)

        u, ts = m.get_by_auth_token(user_id, token)
        self.assertEqual(u, user)
        u, ts = m.get_by_auth_token('fake_user_id', token)
        self.assertEqual(u, None)

        u = m.get_by_auth_password('auth_id_1', 'foo')
        self.assertEqual(u, user)
        self.assertRaises(auth.InvalidPasswordError,
                          m.get_by_auth_password, 'auth_id_1', 'bar')
        self.assertRaises(auth.InvalidAuthIdError,
                          m.get_by_auth_password, 'auth_id_2', 'foo')

    def test_create_user(self):
        m = models.User
        success, info = m.create_user(auth_id='auth_id_1', password_raw='foo')
        self.assertEqual(success, True)
        self.assertTrue(info is not None)
        self.assertTrue(info.password is not None)

        success, info = m.create_user(auth_id='auth_id_1')
        self.assertEqual(success, False)
        self.assertEqual(info, ['auth_id'])

    def test_token(self):
        m = models.UserToken

        auth_id = 'foo'
        subject = 'bar'
        token_1 = m.create(auth_id, subject, token=None)
        token = token_1.token

        token_2 = m.get(user=auth_id, subject=subject, token=token)
        self.assertEqual(token_2, token_1)

        token_3 = m.get(subject=subject, token=token)
        self.assertEqual(token_3, token_1)

        m.get_key(auth_id, subject, token).delete()

        token_2 = m.get(user=auth_id, subject=subject, token=token)
        self.assertEqual(token_2, None)

        token_3 = m.get(subject=subject, token=token)
        self.assertEqual(token_3, None)

    def test_user_token(self):
        m = models.User
        auth_id = 'foo'

        token = m.create_auth_token(auth_id)
        self.assertTrue(m.validate_auth_token(auth_id, token))
        m.delete_auth_token(auth_id, token)
        self.assertFalse(m.validate_auth_token(auth_id, token))

        token = m.create_signup_token(auth_id)
        self.assertTrue(m.validate_signup_token(auth_id, token))
        m.delete_signup_token(auth_id, token)
        self.assertFalse(m.validate_signup_token(auth_id, token))


if __name__ == '__main__':
    test_base.main()
