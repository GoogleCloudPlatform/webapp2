from ndb import model

from experimental.appengine.ndb import unique_model

import test_base

class UniqueConstraintViolation(Exception):
    pass

class User(model.Model):
    username = model.StringProperty(required=True)
    auth_id = model.StringProperty()
    email = model.StringProperty()

class TestUniqueModel(test_base.BaseTestCase):
    def setUp(self):
        super(TestUniqueModel, self).setUp()
        self.register_model('Unique', unique_model.Unique)

    def test_single(self):
        def create_user(username):
            # Assemble the unique scope/value combinations.
            unique_username = 'User.username:%s' % username

            # Create the unique username, auth_id and email.
            success = unique_model.Unique.create(unique_username)

            if success:
                user = User(username=username)
                user.put()
                return user
            else:
                raise UniqueConstraintViolation('Username %s already '
                    'exists' % username)

        user = create_user('username_1')
        self.assertRaises(UniqueConstraintViolation, create_user, 'username_1')

        user = create_user('username_2')
        self.assertRaises(UniqueConstraintViolation, create_user, 'username_2')

    def test_multi(self):
        def create_user(username, auth_id, email):
            # Assemble the unique scope/value combinations.
            unique_username = 'User.username:%s' % username
            unique_auth_id = 'User.auth_id:%s' % auth_id
            unique_email = 'User.email:%s' % email

            # Create the unique username, auth_id and email.
            uniques = [unique_username, unique_auth_id, unique_email]
            success, existing = unique_model.Unique.create_multi(uniques)

            if success:
                user = User(username=username, auth_id=auth_id, email=email)
                user.put()
                return user
            else:
                if unique_username in existing:
                    raise UniqueConstraintViolation('Username %s already '
                        'exists' % username)
                if unique_auth_id in existing:
                    raise UniqueConstraintViolation('Auth id %s already '
                        'exists' % auth_id)
                if unique_email in existing:
                    raise UniqueConstraintViolation('Email %s already '
                        'exists' % email)

        user = create_user('username_1', 'auth_id_1', 'email_1')
        self.assertRaises(UniqueConstraintViolation, create_user, 'username_1', 'auth_id_2', 'email_2')
        self.assertRaises(UniqueConstraintViolation, create_user, 'username_2', 'auth_id_1', 'email_2')
        self.assertRaises(UniqueConstraintViolation, create_user, 'username_2', 'auth_id_2', 'email_1')

        user = create_user('username_2', 'auth_id_2', 'email_2')
        self.assertRaises(UniqueConstraintViolation, create_user, 'username_2', 'auth_id_1', 'email_1')
        self.assertRaises(UniqueConstraintViolation, create_user, 'username_1', 'auth_id_2', 'email_1')
        self.assertRaises(UniqueConstraintViolation, create_user, 'username_1', 'auth_id_1', 'email_2')

    def test_delete_multi(self):
        rv = unique_model.Unique.create_multi(('foo', 'bar', 'baz'))
        self.assertEqual(rv, (True, []))
        rv = unique_model.Unique.create_multi(('foo', 'bar', 'baz'))
        self.assertEqual(rv, (False, ['foo', 'bar', 'baz']))

        unique_model.Unique.delete_multi(('foo', 'bar', 'baz'))

        rv = unique_model.Unique.create_multi(('foo', 'bar', 'baz'))
        self.assertEqual(rv, (True, []))


if __name__ == '__main__':
    test_base.main()
