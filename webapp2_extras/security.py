# -*- coding: utf-8 -*-
"""
    webapp2_extras.security
    =======================

    Security related helpers such as secure password hashing tools and a
    random token generator.

    :copyright: (c) 2010 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import binascii
import hashlib
import hmac
import os

import webapp2


def create_token(bit_strength=64, decimal=False):
    """Generates a random string with the specified bit strength.

    :param bit_strength:
        Bit strength. Must be a multiple of 8.
    :param decimal:
        If True, a decimal representation is returned, otherwise an
        hexadecimal representation is returned.
    :returns:
        A random string with the specified bit strength.
    """
    if bit_strength % 8 or bit_strength <= 0:
        raise ValueError(
            'This function expects a bit strength, got %r.' % bit_strength)

    value = binascii.b2a_hex(os.urandom(bit_strength / 8))
    if decimal:
        value = bytes(int(value, 16))

    return value


def create_password_hash(password, method='sha1', bit_strength=64,
                         pepper=None):
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
    :param bit_strength:
        Bit strength of the salt to be created. Must be a multiple of 8.
    :param pepper:
        A secret constant stored in the application code.
    :returns:
        A formatted hashed string that looks like this::

            method$salt$hash

    This function was ported and adapted from `Werkzeug`_.
    """
    salt = method != 'plain' and create_token(bit_strength) or ''
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
    """Checks if two hash strings are identical."""
    if len(a) != len(b):
        return False

    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)

    return result == 0
