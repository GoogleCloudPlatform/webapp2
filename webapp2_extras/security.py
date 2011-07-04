# -*- coding: utf-8 -*-
"""
    webapp2_extras.security
    =======================

    Security related helpers such as secure password hashing tools and a
    random token generator.

    :copyright: (c) 2010 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import hashlib
import hmac
import os
import random
import string

SALT_CHARS = string.letters + string.digits
_SYS_RNG = random.SystemRandom()


def create_token(length=32):
    """Generates a random string with the specified length.

    This uses ``os.urandom``, which is suitable for cryptographic use.

    See: http://security.stackexchange.com/questions/3936/is-a-rand-from-dev-urandom-secure-for-a-login-key/3939#3939

    :param length:
        Length of the string to be returned.
    :returns:
        A random string with the specified length.

    This function was ported and adapted from `Werkzeug`_.
    """
    if length <= 0:
        raise ValueError(
            'This function expects a positive length, got %r.' % length)

    return ''.join(_SYS_RNG.choice(SALT_CHARS) for _ in xrange(length))


def create_password_hash(password, method='sha1', salt_length=32):
    """Hashes a password.

    The format of the string returned includes the method
    that was used so that :func:`check_password_hash` can check the hash.

    This method can **not** generate unsalted passwords but it is possible
    to set the method to plain to enforce plaintext passwords.  If a salt
    is used, hmac is used internally to salt the password.

    :param password:
        The password to hash.
    :param method:
        The hash method to use (``'md5'`` or ``'sha1'``).
    :param salt_length:
        Length of the salt to be created.
    :returns:
        A formatted hashed string that looks like this::

            method$salt$hash

    This function was ported and adapted from `Werkzeug`_.
    """
    salt = method != 'plain' and create_token(salt_length) or ''
    hashval = hash_password(password, method, salt)
    if hashval is None:
        raise TypeError('Invalid method %r.' % method)

    return '%s$%s$%s' % (hashval, method, salt)


def check_password_hash(password, pwhash):
    """Checks a password against a given salted and hashed password value.

    In order to support unsalted legacy passwords this method supports
    plain text passwords, md5 and sha1 hashes (both salted and unsalted).

    :param password:
        The plaintext password to compare against the hash.
    :param pwhash:
        A hashed string like returned by :func:`create_password_hash`.
    :returns:
        `True` if the password matched, `False` otherwise.

    This function was ported and adapted from `Werkzeug`_.
    """
    if pwhash.count('$') < 2:
        return False

    hashval, method, salt = pwhash.split('$', 2)
    return hash_password(password, method, salt) == hashval


def hash_password(password, method, salt):
    """Hashes a password.

    Supports plaintext without salt, unsalted and salted passwords. In case
    salted passwords are used hmac is used.

    :param password:
        The password to be hashed.
    :param method:
        A method from ``hashlib``, e.g., `sha1` or `md5`, or `plain`.
    :paran salt:
        A random salt string.
    :returns:
        A hashed password.

    This function was ported and adapted from `Werkzeug`_.
    """
    if isinstance(password, unicode):
        password = password.encode('utf-8')

    if method == 'plain':
        return password

    method = getattr(hashlib, method, None)
    if not method:
        return None

    if salt:
        if isinstance(salt, unicode):
            salt = salt.encode('utf-8')

        h = hmac.new(salt, None, method)
    else:
        h = method()

    h.update(password)
    return h.hexdigest()
