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
#: token_max_age
#:     Number of seconds of inactivity after which an auth token is
#:     invalidated. The same value is used to set the ``max_age`` of
#:     persistent auth sessions. Default is 86400 * 7 * 3 (3 weeks).
#:
#: token_interval
#:     Number of seconds after which a new auth token is created and the old
#:     one is invalidated. Default is 86400 (1 day).
default_config = {
    'user_class':      'experimental.appengine.auth.models.User',
    'cookie_name':     'auth',
    'token_max_age':   86400 * 7 * 3,
    'token_interval':  86400,
}


class AnonymousUser(object):
    """"""


class AuthError(Exception):
    """"""


class InvalidUsernameError(AuthError):
    """"""


class InvalidPasswordError(AuthError):
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

        return self.get_user_by_session()

    # Storing and removing user from session ----------------------------------

    def set_user(self, user, token=None, timestamp=None, remember=False,
                 **session_args):
        """Saves a user in the session.

        :param user:
            A User model instance.
        :param token:
            A unique token to be persisted. If None, a new one is created.
        :param timestamp:
            Token creation timestamp. If None, a new one is created.
        :param session_args:
            Keyword arguments to set the session arguments.
        :remember:
            If True, session is set to be persisted.
        """
        token = token or self.user_class.create_auth_token(user.username)
        timestamp = timestamp or int(time.time())
        if remember:
            session_args.setdefault('max_age', self.config['token_max_age'])
        else:
            session_args.setdefault('max_age', None)

        self._set_session_data(user.username, token, timestamp, int(remember),
                               **session_kwargs)
        self._user = user

    def unset_user(self):
        """Removes a user from the session and invalidates the auth token."""
        self._user = None
        data = self._pop_session_data()
        if data:
            # Invalidate current token.
            username, token, timestamp, remember = data
            self.user_class.delete_auth_token(username, token)

    def _set_session_data(self, username, token, timestamp, remember,
                          **session_kwargs):
        self.session['_user'] = [username, token, timestamp, remember]
        self.session.container.session_args.update(session_args)

    def _pop_session_data(self):
        data = self.session.pop('_user', None)
        if isinstance(data, list) and len(data) == 4:
            return data

    # Retrieving a user -------------------------------------------------------

    def get_user_by_session(self):
        """Returns a user based on the current session.

        This essentially retrieves the auth data from the current session and,
        if it is available, returns the result of :meth:`get_user_by_token`
        called using that data.

        :returns:
            A :class:`User` or :class:`AnonymousUser`.
        """
        data = self._pop_session_data()
        if not data:
            return anonymous_user

        # data is username, token, timestamp, remember
        return self.get_user_by_token(*data)

    def get_user_by_token(self, username, token, timestamp=None,
                          remember=False):
        """Returns a user based on ...

        :param username:
        :param token:
        :param timestamp:
        :param remember:
        :returns:
            A :class:`User` or :class:`AnonymousUser`.
        """
        if timestamp:
            age = int(time.time()) - timestamp
            is_expired = age > self.config['token_max_age']
            need_renewal = age > self.config['token_interval']
        else:
            is_expired = need_renewal = False

        user = None
        if not is_expired:
            user = self.user_class.get_by_auth_token(username, token)

        if is_expired or need_renewal:
            # Delete token from db.
            self.user_class.delete_auth_token(username, token)
            token = timestamp = None

        if is_expired or not user:
            return anonymous_user

        self.set_user(user, token=token, timestamp=timestamp,
                      remember=remember)
        return user

    def get_user_by_password(self, username, password, remember=False):
        """Returns a user based on ...

        :param username:
        :param password:
        :param remember:
        :returns:
            A :class:`User` or :class:`AnonymousUser`.
        :raises:
            ``InvalidUsernameError`` or ``InvalidPasswordError``.
        """
        self.unset_user()
        user = self.user_class.get_by_auth_password(username, password)
        if user:
            # Form login always create a new token with new timestamp.
            self.set_user(user, remember=remember)
            return user

        return anonymous_user


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
