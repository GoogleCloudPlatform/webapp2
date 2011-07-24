# -*- coding: utf-8 -*-
"""
    webapp2_extras.auth
    ===================

    Authentication utilities.

    :copyright: 2011 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
import time

import webapp2

from webapp2_extras import security
from webapp2_extras import sessions

#: Default configuration values for this module. Keys are:
#:
#: user_class
#:     User class which implements the API to load and validate users and
#:     tokens. Can also be a string in dotted notation to be lazily imported.
#:     Default is :class:`experimental.auth.models.User`.
#:
#: cookie_name
#:     Name of the cookie to save the auth session. Default is `auth`.
#:
#: token_expiration
#:     Number of seconds of inactivity after which an auth token is
#:     invalidated. The same value is used to set the ``max_age`` of the
#:     auth session. Default is 86400 * 7 * 3 (3 weeks).
#:
#: token_interval
#:     Number of seconds after which a new auth token is created and the old
#:     one is invalidated. Default is 86400 (1 day).
default_config = {
    'user_class':      'experimental.auth.models.User',
    'cookie_name':     'auth',
    'token_expiration': 86400 * 7 * 3,
    'token_interval':   86400,
}


class AnonymousUser(object):
    """"""


class AuthException(Exception):
    """"""


class InvalidUsernameError(AuthException):
    """"""


class InvalidPasswordError(AuthException):
    """"""


class Auth(object):
    """"""

    #: Configuration key.
    config_key = __name__

    #: Internal stuff.
    _user = None

    def __init__(self, request, config=None):
        """Initializes the session store.

        :param request:
            A :class:`webapp2.Request` instance.
        :param config:
            A dictionary of configuration values to be overridden. See
            the available keys in :data:`default_config`.
        """
        self.request = request
        # Base configuration.
        self.config = request.app.config.load_config(self.config_key,
            default_values=default_config, user_values=config)

    @webapp2.cached_property
    def user_class(self):
        cls = self.config['user_class']
        if isinstance(cls, basestring):
            cls = self.config['user_class'] = webapp2.import_string(cls)

        return cls

    @webapp2.cached_property
    def session(self):
        store = sessions.get_store(request=self.request)
        return store.get_session(self.config['cookie_name'])

    @property
    def user(self):
        if self._user:
            return self._user

        return self.load_from_session()

    def set_user(self, user, token=None, timestamp=None, remember=False):
        """Saves a user in the session."""
        token = token or self.user_class.create_auth_token(user.username)
        timestamp = timestamp or int(time.time())

        self.session['_user'] = [
            user.username,
            token,
            timestamp,
            int(remember),
        ]

        session_args = self.session.container.session_args
        if remember:
            # TODO: do we need a separate config for this?
            session_args['max_age'] = self.config['token_expiration']
        else:
            session_args['max_age'] = None

        self._user = user

    def unset_user(self):
        """Removes a user from the session and invalidates the auth token."""
        self._user = None
        data = self._pop_session_data()
        if data:
            # Invalidate current token.
            username, token, timestamp, remember = data
            self.user_class.delete_auth_token(username, token)

    def load_from_session(self):
        data = self._pop_session_data()
        if not data:
            return anonymous_user

        # timestamp is from the token creation
        username, token, timestamp, remember = data
        age = int(time.time()) - timestamp
        is_expired = age > self.config['token_expiration']
        need_renewal = age > self.config['token_interval']

        user = None
        if not is_expired:
            user = self.user_class.get_by_auth_token(username, token)

        if is_expired or need_renewal:
            # Delete token from db.
            self.user_class.delete_auth_token(username, token)
            token = None
            timestamp = None

        if is_expired or not user:
            return anonymous_user

        self.set_user(user, token=token, timestamp=timestamp,
                      remember=remember)
        return user

    def load_from_form(self, username, password, remember=False):
        """
        :raises:
            ``InvalidUsernameError`` or ``InvalidPasswordError``.
        """
        user = self.user_class.get_by_username_and_password(username,
                                                            password)
        if user:
            # Form login always create a new token with new timestamp.
            self.set_user(user, remember=remember)
            return user

        return anonymous_user

    def _pop_session_data(self):
        data = self.session.pop('_user', None)
        if isinstance(data, list) and len(data) == 4:
            return data


# Factories -------------------------------------------------------------------


#: Key used to store :class:`Auth` in the request registry.
_registry_key = 'webapp2_extras.auth.Auth'


def get_auth(factory=Auth, key=_registry_key, request=None):
    """Returns an instance of :class:`Auth` from the request registry.

    It'll try to get it from the current request registry, and if it is not
    registered it'll be instantiated and registered. A second call to this
    function will return the same instance.

    :param factory:
        The callable used to build and register the instance if it is not yet
        registered. The default is the class :class:`Auth` itself.
    :param key:
        The key used to store the instance in the registry. A default is used
        if it is not set.
    :param request:
        A :class:`webapp2.Request` instance used to store the instance. The
        active request is used if it is not set.
    """
    request = request or webapp2.get_request()
    auth = request.registry.get(key)
    if not auth:
        auth = request.registry[key] = factory(request)

    return auth


def set_auth(auth, key=_registry_key, request=None):
    """Sets an instance of :class:`Auth` in the request registry.

    :param auth:
        An instance of :class:`Auth`.
    :param key:
        The key used to retrieve the instance from the registry. A default
        is used if it is not set.
    :param request:
        A :class:`webapp2.Request` instance used to retrieve the instance. The
        active request is used if it is not set.
    """
    request = request or webapp2.get_request()
    request.registry[key] = auth


anonymous_user = AnonymousUser()
