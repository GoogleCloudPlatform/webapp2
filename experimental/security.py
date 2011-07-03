# -*- coding: utf-8 -*-
"""


    Security related helpers such as secure password hashing tools.

    :copyright: (c) 2010 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import hmac
import string
from random import SystemRandom

# because the API of hmac changed with the introduction of the
# new hashlib module, we have to support both.  This sets up a
# mapping to the digest factory functions and the digest modules
# (or factory functions with changed API)
try:
    from hashlib import sha1 as _sha1_mod, md5 as _md5_mod
    _hash_funcs = _hash_mods = {'sha1': _sha1_mod, 'md5': _md5_mod}
except ImportError:
    import sha as _sha1_mod, md5 as _md5_mod
    _hash_mods = {'sha1': _sha1_mod, 'md5': _md5_mod}
    _hash_funcs = {'sha1': _sha1_mod.new, 'md5': _md5_mod.new}

SALT_CHARS = string.letters + string.digits
_sys_rng = SystemRandom()


def generate_token(length=32):
    """Generates a random string of characters with specified `length`.

    :param length:
        Length of the token to be returned.
    :returns:
        A random string.

    This function comes from `Werkzeug`_.
    """
    if length <= 0:
        raise ValueError('Requested salt of length <= 0')

    return ''.join(_sys_rng.choice(SALT_CHARS) for _ in xrange(length))


def generate_password_hash(password, method='sha1', salt_length=8):
    """Hashes a password.

    The format of the string returned includes the method
    that was used so that :func:`check_password_hash` can check the hash.

    The format for the hashed string looks like this::

        method$salt$hash

    This method can **not** generate unsalted passwords but it is possible
    to set the method to plain to enforce plaintext passwords.  If a salt
    is used, hmac is used internally to salt the password.

    :param password:
        The password to hash.
    :param method:
        The hash method to use (``'md5'`` or ``'sha1'``).
    :param salt_length:
        The lengt of the salt in letters.

    This function comes from `Werkzeug`_.
    """
    salt = method != 'plain' and generate_token(salt_length) or ''
    h = _hash_internal(method, salt, password)
    if h is None:
        raise TypeError('invalid method %r' % method)

    return '%s$%s$%s' % (method, salt, h)


def check_password_hash(pwhash, password):
    """Checks a password against a given salted and hashed password value.

    In order to support unsalted legacy passwords this method supports
    plain text passwords, md5 and sha1 hashes (both salted and unsalted).

    :param pwhash:
        A hashed string like returned by :func:`generate_password_hash`.
    :param password:
        The plaintext password to compare against the hash.
    :returns:
        `True` if the password matched, `False` otherwise.

    This function comes from `Werkzeug`_.
    """
    if pwhash.count('$') < 2:
        return False

    method, salt, hashval = pwhash.split('$', 2)
    return _hash_internal(method, salt, password) == hashval


def _hash_internal(method, salt, password):
    """Internal password hash helper.

    Supports plaintext without salt, unsalted and salted passwords. In case
    salted passwords are used hmac is used.
    """
    if method == 'plain':
        return password

    if salt:
        if method not in _hash_mods:
            return None

        if isinstance(salt, unicode):
            salt = salt.encode('utf-8')

        h = hmac.new(salt, None, _hash_mods[method])
    else:
        if method not in _hash_funcs:
            return None

        h = _hash_funcs[method]()

    if isinstance(password, unicode):
        password = password.encode('utf-8')

    h.update(password)
    return h.hexdigest()
