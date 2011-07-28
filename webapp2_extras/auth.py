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
#: user_model
#:     User model which implements the API to load and validate users and
#:     tokens. Can also be a string in dotted notation to be lazily imported.
#:     Default is :class:`webapp2_extras.appengine.auth.models.User`.
#:
#: session_backend
#:     Name of the session backend to be used. Default is `securecookie`.
#:
#: cookie_name
#:     Name of the cookie to save the auth session. Default is `auth`.
#:
#: token_max_age
#:     Number of seconds of inactivity after which an auth token is
#:     invalidated. The same value is used to set the ``max_age`` for
#:     persistent auth sessions. Default is 86400 * 7 * 3 (3 weeks).
#:
#: token_new_age
#:     Number of seconds after which a new token is written to the database.
#:     Use this to limit database writes; set to None to write on all requests.
#:     Default is 86400 (1 day).
#:
#: token_cache_age
#:     Number of seconds after which a token must be checked in the database.
#:     Use this to limit database reads; set to None to read on all requests.
#:     Default is 3600 (1 hour).
#:
#: user_attributes
#:     A list of extra user attributes to be stored in the session.
#      The user object must provide all of them as attributes.
#:     Default is an empty list.
default_config = {
    'user_model':      'webapp2_extras.appengine.auth.models.User',
    'session_backend': 'securecookie',
    'cookie_name':     'auth',
    'token_max_age':   86400 * 7 * 3,
    'token_new_age':   86400,
    'token_cache_age': 3600,
    'user_attributes': [],
}


class AnonymousUser(object):
    """TODO"""


class AuthError(Exception):
    """Base auth exception."""


class InvalidAuthIdError(AuthError):
    """Raised when a user can't be fetched given an auth_id."""


class InvalidPasswordError(AuthError):
    """Raised when a user password doesn't match."""


class AuthStore(object):
    """Provides common utilities and configuration for :class:`Auth`."""

    #: Configuration key.
    config_key = __name__

    #: Attributes stored in a session.
    session_attributes = ['auth_id', 'remember',
                          'token', 'token_ts', 'cache_ts']

    def __init__(self, app, config=None):
        """Initializes the session store.

        :param app:
            A :class:`webapp2.WSGIApplication` instance.
        :param config:
            A dictionary of configuration values to be overridden. See
            the available keys in :data:`default_config`.
        """
        self.app = app
        # Base configuration.
        self.config = app.config.load_config(self.config_key,
            default_values=default_config, user_values=config)

    # User model related ------------------------------------------------------

    @webapp2.cached_property
    def user_model(self):
        """Configured user model."""
        cls = self.config['user_model']
        if isinstance(cls, basestring):
            cls = self.config['user_model'] = webapp2.import_string(cls)

        return cls

    def user_to_dict(self, user):
        """

        :param user:
            TODO
        :returns:
            TODO
        """
        if not user:
            return None

        attrs = self.config['user_attributes'] + ['auth_id']
        return dict((a, getattr(user, a)) for a in attrs)

    def get_user_by_auth_password(self, auth_id, password):
        """

        :param auth_id:
            TODO
        :param password:
            TODO
        :returns:
            user dict
        :raises:
            ``InvalidAuthIdError`` or ``InvalidPasswordError``.
        """
        user = self.user_model.get_by_auth_password(auth_id, password)
        return self.user_to_dict(user)

    def get_user_by_auth_token(self, auth_id, token):
        """

        :param auth_id:
            TODO
        :param token:
            TODO
        :returns:
            (user_dict, token_timestamp)
        """
        user, ts = self.user_model.get_by_auth_token(auth_id, token)
        return self.user_to_dict(user), ts

    def create_auth_token(self, auth_id):
        """

        :param auth_id:
            TODO
        :returns:
            token
        """
        return self.user_model.create_auth_token(auth_id)

    def delete_auth_token(self, auth_id, token):
        """"""
        return self.user_model.delete_auth_token(auth_id, token)

    # Session related ---------------------------------------------------------

    def get_session(self, request):
        """Returns an auth session.

        :param request:
            A :class:`webapp2.Request` instance.
        :returns:
            A session dict.
        """
        store = sessions.get_store(request=request)
        return store.get_session(self.config['cookie_name'],
                                 backend=self.config['session_backend'])

    def deserialize_session(self, data):
        """Deserializes values for a session.

        :param data:
            A list with session data.
        :returns:
            A dict with session data.
        """
        attrs = self.session_attributes + self.config['user_attributes']
        assert len(data) == len(attrs)
        return dict(zip(attrs, data))

    def serialize_session(self, data):
        """Serializes values for a session.

        :param data:
            A dict with session data.
        :returns:
            A list with session data.
        """
        attrs = self.session_attributes + self.config['user_attributes']
        assert len(data) == len(attrs)
        return [data.get(k) for k in attrs]

    # Validators --------------------------------------------------------------

    def set_password_validator(self, func):
        """

        :param func:
            A function that receives ``(store, auth_id, password)``
            and returns ...
        """
        self.validate_password = func.__get__(self, self.__class__)

    def set_token_validator(self, func):
        """

        :param func:
            A function that receives ``(store, auth_id, token, token_ts)``
            and returns ...
        """
        self.validate_token = func.__get__(self, self.__class__)

    def default_password_validator(self, auth_id, password):
        """Validates a password.

        Passwords are used to log-in using forms or to request auth tokens
        from services.

        :param auth_id:
            Auth_id.
        :param password:
            Password to be checked.
        :returns:
            user or None
        :raises:
            ``InvalidAuthIdError`` or ``InvalidPasswordError``.
        """
        return self.get_user_by_auth_password(auth_id, password)

    def default_token_validator(self, auth_id, token, token_ts=None):
        """Validates a token.

        Tokens are random strings used to authenticate temporarily. They are
        used to validate sessions or service requests.

        :param auth_id:
            Auth_id.
        :param token:
            Token to be checked.
        :param token_ts:
            Optional token timestamp used to pre-validate the token age.
        :returns:
            A tuple ``(user, token)``.
        """
        now = int(time.time())
        delete = token_ts and ((now - token_ts) > self.config['token_max_age'])
        create = False

        if not delete:
            # Try to fetch the user.
            user, ts = self.get_user_by_auth_token(auth_id, token)
            if user:
                # Now validate the real timestamp.
                delete = (now - ts) > self.config['token_max_age']
                create = (now - ts) > self.config['token_new_age']

        if delete or create or not user:
            if delete or create:
                # Delete token from db.
                self.delete_auth_token(auth_id, token)

                if delete:
                    user = None

            token = None

        return user, token

    validate_password = default_password_validator
    validate_token = default_token_validator


class Auth(object):
    """Authentication provider for a single request."""

    #: A :class:`webapp2.Request` instance.
    request = None
    #: An :class:`AuthStore` instance.
    store = None
    #: Caches user for the request.
    _user = None

    def __init__(self, request):
        """Initializes the auth provider for a request.

        :param request:
            A :class:`webapp2.Request` instance.
        """
        self.request = request
        self.store = get_store(app=request.app)

    # Retrieving a user -------------------------------------------------------

    def get_user_by_session(self):
        """Returns a user based on ...

        :param:
            TODO
        :returns:
            TODO
        """
        # TODO

    def get_user_by_token(self, auth_id, token, cache=None, cache_ts=None):
        """Returns a user based on ...

        :param:
            TODO
        :param:
            TODO
        :param:
            TODO
        :param:
            TODO
        :returns:
            TODO
        """
        # TODO

    def get_user_by_password(self, auth_id, password, remember=False,
                             save_session=True):
        """Returns a user based on ...

        :param auth_id:
        :param password:
        :param remember:
            If True, saves permanent sessions.
        :param save_session:
        :returns:
            A :class:`User` or :class:`AnonymousUser`.
        :raises:
            ``InvalidAuthIdError`` or ``InvalidPasswordError``.
        """
        if save_session:
            # During a login attempt, invalidate current session.
            self.unset_session()

        user = self.store.validate_password(auth_id, password)
        if not user:
            user = anonymous_user
        elif save_session:
            # This always creates a new token with new timestamp.
            self.set_session(user, remember=remember)

        self._user = user
        return user

    # Storing and removing user from session ----------------------------------

    @webapp2.cached_property
    def session(self):
        """Auth session."""
        return self.store.get_session(self.request)

    def set_session(self, user, token=None, token_ts=None, cache_ts=None,
                    remember=False, **session_args):
        """Saves a user in the session.

        :param user:
            A dictionary with user data.
        :param token:
            A unique token to be persisted. If None, a new one is created.
        :param token_ts:
            Token timestamp. If None, a new one is created.
        :param cache_ts:
            Token cache timestamp. If None, a new one is created.
        :remember:
            If True, session is set to be persisted.
        :param session_args:
            Keyword arguments to set the session arguments.
        """
        now = int(time.time())
        token = token or self.store.create_auth_token(user['auth_id'])
        token_ts = token_ts or now
        cache_ts = cache_ts or now
        if remember:
            max_age = self.store.config['token_max_age']
        else:
            max_age = None

        session_args.setdefault('max_age', max_age)
        data = dict(user)
        data.update({
            'token':    token,
            'token_ts': token_ts,
            'cache_ts': cache_ts,
            'remember': int(remember),
        })
        self.set_session_data(data, **session_args)
        self._user = user

    def unset_session(self):
        """Removes a user from the session and invalidates the auth token."""
        self._user = None
        data = self.get_session_data(pop=True)
        if data:
            # Invalidate current token.
            self.store.delete_auth_token(data['auth_id'], data['token'])

    def get_session_data(self, pop=False):
        """

        :param pop:
            If True, removes the session.
        :returns:
            A deserialized session, or None.
        """
        func = self.session.pop if pop else self.session.get
        rv = func('_user', None)
        if rv:
            return self.store.deserialize_session(rv)

    def set_session_data(self, data, **session_args):
        """

        :param data:
            Deserialized session data.
        :param session_args:
            Extra arguments for the session.
        """
        self.session['_user'] = self.store.serialize_session(data)
        self.session.container.session_args.update(session_args)


# Factories -------------------------------------------------------------------

#: Key used to store :class:`AuthStore` in the app registry.
_store_registry_key = 'webapp2_extras.auth.Auth'
#: Key used to store :class:`Auth` in the request registry.
_auth_registry_key = 'webapp2_extras.auth.Auth'


def get_store(factory=AuthStore, key=_store_registry_key, app=None):
    """Returns an instance of :class:`AuthStore` from the app registry.

    It'll try to get it from the current app registry, and if it is not
    registered it'll be instantiated and registered. A second call to this
    function will return the same instance.

    :param factory:
        The callable used to build and register the instance if it is not yet
        registered. The default is the class :class:`AuthStore` itself.
    :param key:
        The key used to store the instance in the registry. A default is used
        if it is not set.
    :param app:
        A :class:`webapp2.WSGIApplication` instance used to store the instance.
        The active app is used if it is not set.
    """
    app = app or webapp2.get_app()
    store = app.registry.get(key)
    if not store:
        store = app.registry[key] = factory(app)

    return store


def set_store(store, key=_store_registry_key, app=None):
    """Sets an instance of :class:`AuthStore` in the app registry.

    :param store:
        An instance of :class:`AuthStore`.
    :param key:
        The key used to retrieve the instance from the registry. A default
        is used if it is not set.
    :param request:
        A :class:`webapp2.WSGIApplication` instance used to retrieve the
        instance. The active app is used if it is not set.
    """
    app = app or webapp2.get_app()
    app.registry[key] = store


def get_auth(factory=Auth, key=_auth_registry_key, request=None):
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


def set_auth(auth, key=_auth_registry_key, request=None):
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


#: A singleton anonymous user.
anonymous_user = AnonymousUser()
