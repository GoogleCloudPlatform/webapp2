from ndb import model

from webapp2_extras import security
from experimental import unique_model


class User(model.Model):
    created = model.DateTimeProperty(auto_now_add=True)
    updated = model.DateTimeProperty(auto_now=True)
    # Display name: username as typed by the user.
    name = model.StringProperty(required=True)
    # Username in lower case. UNIQUE.
    username = model.StringProperty(required=True)
    # ID for third party authentication, e.g. 'google:username'. UNIQUE.
    auth_id = model.StringProperty(required=True)
    # Hashed password. Can be null because third party authentication
    # doesn't have a password.
    password = model.StringProperty()
    # Primary email address. UNIQUE.
    email = model.StringProperty(required=True)
    # Account status:
    # 0: not confirmed account
    # 1: normal user
    # 2: admin
    # 3 etc: to be defined
    status = model.IntegerProperty(default=0)

    @classmethod
    def get_key(cls, username):
        return model.Key(cls, username.lower())

    @property
    def is_admin(self):
        return self.status == 2

    @property
    def is_active(self):
        return self.status != 0

    @classmethod
    def get_by_username(cls, username):
        key = cls.get_key(username)
        return key.get()

    @classmethod
    def get_by_auth_id(cls, auth_id):
        query = cls.query(cls.auth_id == auth_id)
        return query.get()

    @classmethod
    def get_by_email(cls, email):
        query = cls.query(cls.email == email)
        return query.get()

    @classmethod
    def get_by_auth_token(cls, username, token):
        token_key = UserToken.get_key(username, 'auth', token)
        user_key = cls.get_key(username)
        # Use get_multi() to save a RPC call.
        valid_token, user = model.get_multi([token_key, user_key])
        if valid_token and user:
            return user

    @classmethod
    def validate_username_and_password(cls, username, password):
        """Returns (user, reason-if-not-valid)."""
        # TODO: check if user.status != 0 here?
        user = cls.get_by_username(username)
        if not user:
            return None, 'invalid-username'

        if not security.check_password_hash(password, user.password):
            return None, 'invalid-password'

        return user, None

    @classmethod
    def validate_token(cls, subject, token):
        return UserToken.get_by_subject_token(subject, token)

    @classmethod
    def validate_registration_token(cls, token):
        return cls.validate_token('confirm-registration', token)

    @classmethod
    def delete_auth_token(cls, username, token):
        """Interface method that just delegates to UserToken."""
        UserToken.delete_by_username_subject_token(username, 'auth', token)

    @classmethod
    def create_auth_token(self, username):
        entity = UserToken.create(username, 'auth', token_size=64)
        return entity.token

    @classmethod
    def create_signup_token(self, username):
        entity = UserToken.create(username, 'confirm-signup')
        return entity.token

    @classmethod
    def register(cls, **user_values):
        """Registers a new user."""
        if 'password_raw' in user_values:
            user_values['password'] = security.create_password_hash(
                user_values.pop('password_raw'), bit_strength=12)

        user_values['username'] = username = user_values['name'].lower()
        user = User(key=cls.get_key(username), **user_values)

        # Unique auth id and email.
        unique_auth_id = 'User.auth_id:%s' % user_values['auth_id']
        unique_email = 'User.email:%s' % user_values['email']
        uniques = [unique_auth_id, unique_email]
        success, existing = unique_model.Unique.create_multi(uniques)

        if success:
            txn = lambda: user.put() if not user.key.get() else None
            if model.transaction(txn):
                return True, user
            else:
                unique_model.Unique.delete_multi(uniques)
                return False, ['username']
        else:
            properties = []
            if unique_auth_id in uniques:
                properties.append('auth_id')

            if unique_email in uniques:
                properties.append('email')

            return False, properties


class UserToken(model.Model):
    created = model.DateTimeProperty(auto_now_add=True)
    updated = model.DateTimeProperty(auto_now=True)
    username = model.StringProperty(required=True, indexed=False)
    subject = model.StringProperty(required=True)
    token = model.StringProperty(required=True)

    @classmethod
    def get_key(cls, username, subject, token):
        return model.Key(cls, '%s.%s.%s' % (username, subject, token))

    @classmethod
    def create(cls, username, subject, token=None, token_size=32):
        token = token or security.create_token(token_size)
        key = cls.get_key(username, subject, token)
        entity = cls(key=key, username=username, subject=subject, token=token)
        entity.put()
        return entity

    @classmethod
    def get_by_username_subject_token(cls, username, subject, token):
        key = cls.get_key(username, subject, token)
        return key.get()

    @classmethod
    def get_by_subject_token(cls, subject, token):
        query = cls.query(cls.subject == subject, cls.token == token)
        return query.get()

    @classmethod
    def delete_by_username_subject_token(cls, username, subject, token):
        key = cls.get_key(username, subject, token)
        return key.delete()
