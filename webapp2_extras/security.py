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
import random
import string

import webapp2

_rng = random.SystemRandom()
_chars = string.letters + string.digits


def create_token(length=22):
    """Generates a random string with the specified length.

    :param length:
        Length of the token to be created. Default is 22 (128 bits entropy).
        The following table shows how to achieve different entropies:

          =========  =========
          Entropy    Length
          =========  =========
          32 bits	 6
          40 bits	 7
          64 bits	 11
          80 bits	 14
          96 bits    17
          128 bits   22
          160 bits   27
          192 bits   33
          224 bits   38
          256 bits   43
          =========  =========

    :returns:
        A random string using case sensitive alphanumeric characters and
        the specified length.

    This function was ported and adapted from `Werkzeug`_.
    """
    if length <= 0:
        raise ValueError(
            'Token length must be greater than 0, got %r.' % length)

    return ''.join(_rng.choice(_chars) for _ in xrange(length))


def create_password_hash(password, method='sha1', length=22, pepper=None):
    """Hashes a password.

    The format of the string returned includes the method that was used
    so that :func:`check_password_hash` can check the hash.

    This method can **not** generate unsalted passwords but it is possible
    to set the method to plain to enforce plaintext passwords. If a salt
    is used, hmac is used internally to salt the password.

    :param password:
        The password to hash.
    :param method:
        The hash method to use (``'md5'`` or ``'sha1'``).
    :param length:
        Length of the salt to be created.
    :param pepper:
        A secret constant stored in the application code.
    :returns:
        A formatted hashed string that looks like this::

            method$salt$hash

    This function was ported and adapted from `Werkzeug`_.
    """
    salt = method != 'plain' and create_token(length) or ''
    hashval = hash_password(password, method, salt, pepper)
    if hashval is None:
        raise TypeError('Invalid method %r.' % method)

    return '%s$%s$%s' % (hashval, method, salt)


def check_password_hash(password, pwhash, pepper=None):
    """Checks a password against a given salted and hashed password value.

    In order to support unsalted legacy passwords this method supports
    plain text passwords, md5 and sha1 hashes (both salted and unsalted).

    :param password:
        The plaintext password to compare against the hash.
    :param pwhash:
        A hashed string like returned by :func:`create_password_hash`.
    :param pepper:
        A secret constant stored in the application code.
    :returns:
        `True` if the password matched, `False` otherwise.

    This function was ported and adapted from `Werkzeug`_.
    """
    if pwhash.count('$') < 2:
        return False

    hashval, method, salt = pwhash.split('$', 2)
    return hash_password(password, method, salt, pepper) == hashval


def hash_password(password, method, salt=None, pepper=None):
    """Hashes a password.

    Supports plaintext without salt, unsalted and salted passwords. In case
    salted passwords are used hmac is used.

    :param password:
        The password to be hashed.
    :param method:
        A method from ``hashlib``, e.g., `sha1` or `md5`, or `plain`.
    :param salt:
        A random salt string.
    :param pepper:
        A secret constant stored in the application code.
    :returns:
        A hashed password.

    This function was ported and adapted from `Werkzeug`_.
    """
    password = webapp2._to_utf8(password)
    if method == 'plain':
        return password

    method = getattr(hashlib, method, None)
    if not method:
        return None

    if salt:
        h = hmac.new(webapp2._to_utf8(salt), password, method)
    else:
        h = method(password)

    if pepper:
        h = hmac.new(webapp2._to_utf8(pepper), h.hexdigest(), method)

    return h.hexdigest()


def compare_hashes(a, b):
    """Checks if two hash strings are identical.

    The intention is to make the running time be less dependant on the size of
    the string.

    :param a:
        String 1.
    :param b:
        String 2.
    :returns:
        True if both strings are equal, False otherwise.
    """
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)

    return result == 0
