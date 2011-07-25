from experimental.appengine.auth import models

import test_base


class TestAuthModels(test_base.BaseTestCase):
    def test_create_user(self):
        success, info = models.User.create_user(name='name_1',
            username='username_1', auth_id='auth_id_1', email='email_1',
            password_raw='foo')
        self.assertEqual(success, True)
        self.assertTrue(info is not None)

        success, info = models.User.create_user(name='name_1',
            username='username_1', auth_id='auth_id_1', email='email_1')
        self.assertEqual(success, False)
        self.assertEqual(info, ['auth_id', 'email'])

        success, info = models.User.create_user(name='name_1',
            username='username_1', auth_id='auth_id_2', email='email_2')
        self.assertEqual(success, False)
        self.assertEqual(info, ['username'])

        success, info = models.User.create_user(name='name_1',
            username='username_2', auth_id='auth_id_2', email='email_1',
            _unique_email=False)
        self.assertEqual(success, True)
        self.assertTrue(info is not None)

    def test_token(self):
        m = models.UserToken

        username = 'foo'
        subject = 'bar'
        token_1 = m.create(username, subject, token=None, token_size=32)
        token = token_1.token

        token_2 = m.get(username=username, subject=subject, token=token)
        self.assertEqual(token_2, token_1)

        token_3 = m.get(subject=subject, token=token)
        self.assertEqual(token_3, token_1)

        m.get_key(username, subject, token).delete()

        token_2 = m.get(username=username, subject=subject, token=token)
        self.assertEqual(token_2, None)

        token_3 = m.get(subject=subject, token=token)
        self.assertEqual(token_3, None)

    def test_user_token(self):
        m = models.User
        username = 'foo'

        token = m.create_auth_token(username)
        self.assertTrue(m.validate_auth_token(username, token))
        m.delete_auth_token(username, token)
        self.assertFalse(m.validate_auth_token(username, token))

        token = m.create_signup_token(username)
        self.assertTrue(m.validate_signup_token(username, token))
        m.delete_signup_token(username, token)
        self.assertFalse(m.validate_signup_token(username, token))


if __name__ == '__main__':
    test_base.main()
