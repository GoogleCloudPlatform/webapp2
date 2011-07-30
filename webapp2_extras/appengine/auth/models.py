# -*- coding: utf-8 -*-
"""
    webapp2_extras.appengine.auth.models
    ====================================

    Auth related models.

    :copyright: 2011 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
import time

from ndb import model

from webapp2_extras import security

from webapp2_extras import auth
from webapp2_extras.appengine.ndb import unique_model


class User(model.Model):
    """"""

    created = model.DateTimeProperty(auto_now_add=True)
    updated = model.DateTimeProperty(auto_now=True)
    # ID for third party authentication, e.g. 'google:username'. UNIQUE.
    auth_ids = model.StringProperty(repeated=True)
    # Hashed password. Not required because third party authentication
    # doesn't use password.
    password = model.StringProperty()

    @classmethod
    def get_key(cls, user_id):
        return model.Key(cls, user_id)

    @classmethod
    def get_by_auth_id(cls, auth_id):
        return cls.query(cls.auth_ids == auth_id.lower()).get()

    @classmethod
    def get_by_auth_token(cls, user_id, token):
        token_key = UserToken.get_key(user_id, 'auth', token)
        user_key = cls.get_key(user_id)
        # Use get_multi() to save a RPC call.
        valid_token, user = model.get_multi([token_key, user_key])
        if valid_token and user:
            timestamp = int(time.mktime(valid_token.created.timetuple()))
            return user, timestamp

        return None, None

    @classmethod
    def get_by_auth_password(cls, auth_id, password):
        """Returns user, validating password.
        :param auth_id:
            Authentication id.
        :param password:
            Password to be checked.

        :raises:
            ``auth.InvalidAuthIdError`` or ``auth.InvalidPasswordError``.
        """
        user = cls.get_by_auth_id(auth_id)
        if not user:
            raise auth.InvalidAuthIdError()

        if not security.check_password_hash(password, user.password):
            raise auth.InvalidPasswordError()

        return user

    @classmethod
    def validate_token(cls, user_id, subject, token):
        return UserToken.get(user=user_id, subject=subject,
                             token=token) is not None

    @classmethod
    def create_auth_token(cls, user_id):
        return UserToken.create(user_id, 'auth').token

    @classmethod
    def validate_auth_token(cls, user_id, token):
        return cls.validate_token(user_id, 'auth', token)

    @classmethod
    def delete_auth_token(cls, user_id, token):
        UserToken.get_key(user_id, 'auth', token).delete()

    @classmethod
    def create_signup_token(cls, user_id):
        entity = UserToken.create(user_id, 'signup')
        return entity.token

    @classmethod
    def validate_signup_token(cls, user_id, token):
        return cls.validate_token(user_id, 'signup', token)

    @classmethod
    def delete_signup_token(cls, user_id, token):
        UserToken.get_key(user_id, 'signup', token).delete()

    @classmethod
    def create_user(cls, auth_id, **user_values):
        """Creates a new user.

        :param auth_id:
            A string that is unique to the user. User many have
            multiple auth ids.

            Example auth ids:

            - own:username
            - google:username
            - yahoo:username

            The properties values of `auth_id` must be unique.
        :param _unique_email:
            True to require the email to be unique, False otherwise.
        :param user_values:
            Keyword arguments to create a new user entity.

            Optional keywords:

            - password_raw (a plain password to be hashed)
        :returns:
            A tuple (boolean, info). The boolean indicates if the user
            was created. If creation succeeds,  ``info`` is the user entity;
            otherwise it is a list of duplicated unique properties that
            caused the creation to fail.
        """
        assert user_values.get('password') is None, \
            'Use password_raw instead of password to create new users'

        if 'password_raw' in user_values:
            user_values['password'] = security.generate_password_hash(
                user_values.pop('password_raw'), length=12)

        auth_id = auth_id.lower()
        user_values['auth_ids'] = [auth_id]
        user = User(**user_values)

        # Unique auth id and email.
        unique_auth_id = 'User.auth_id:%s' % auth_id

        uniques = [unique_auth_id]

        success, existing = unique_model.Unique.create_multi(uniques)

        if success:
            user.put()
            return True, user
        else:
            properties = []

            if unique_auth_id in existing:
                properties.append('auth_id')

            return False, properties


class UserToken(model.Model):
    """Stores validation tokens for users."""

    created = model.DateTimeProperty(auto_now_add=True)
    updated = model.DateTimeProperty(auto_now=True)
    user = model.StringProperty(required=True, indexed=False)
    subject = model.StringProperty(required=True)
    token = model.StringProperty(required=True)

    @classmethod
    def get_key(cls, user, subject, token):
        """Returns a token key."""
        return model.Key(cls, '%s.%s.%s' % (str(user), subject, token))

    @classmethod
    def create(cls, user, subject, token=None):
        """Fetches a user token."""
        user = str(user)
        token = token or security.generate_random_string(entropy=64)
        key = cls.get_key(user, subject, token)
        entity = cls(key=key, user=user, subject=subject, token=token)
        entity.put()
        return entity

    @classmethod
    def get(cls, user=None, subject=None, token=None):
        """Fetches a user token."""
        if user and subject and token:
            return cls.get_key(user, subject, token).get()

        assert subject and token, \
            'subject and token must be provided to UserToken.get().'
        return cls.query(cls.subject==subject, cls.token==token).get()