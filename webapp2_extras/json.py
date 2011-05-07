# -*- coding: utf-8 -*-
"""
    webapp2_extras.json
    ===================

    JSON helpers for webapp2.

    :copyright: 2011 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
import base64
import urllib

from django.utils import simplejson as json


def encode(value, *args, **kwargs):
    """Serializes a value to JSON.

    :param value:
        A value to be serialized.
    :param args:
        Extra arguments to be passed to `json.dumps()`.
    :param kwargs:
        Extra keyword arguments to be passed to `json.dumps()`.
    :returns:
        The serialized value.
    """
    # JSON permits but does not require forward slashes to be escaped.
    # This is useful when json data is emitted in a <script> tag
    # in HTML, as it prevents </script> tags from prematurely terminating
    # the javscript.  Some json libraries do this escaping by default,
    # although python's standard library does not, so we do it here.
    # http://stackoverflow.com/questions/1580647/json-why-are-forward-slashes-escaped
    kwargs.setdefault('separators', (',', ':'))
    return json.dumps(value, *args, **kwargs).replace("</", "<\\/")


def decode(value, *args, **kwargs):
    """Deserializes a value from JSON.

    :param value:
        A value to be deserialized.
    :param args:
        Extra arguments to be passed to `json.loads()`.
    :param kwargs:
        Extra keyword arguments to be passed to `json.loads()`.
    :returns:
        The deserialized value.
    """
    if isinstance(value, str):
        value = value.decode('utf-8')

    assert isinstance(value, unicode)
    return json.loads(value, *args, **kwargs)


def b64encode(value):
    """Serializes a value to JSON and encodes it using base64.

    :param value:
        A value to be encoded.
    :returns:
        The encoded value.
    """
    return base64.b64encode(encode(value))


def b64decode(value):
    """Decodes a value using base64 and deserializes it from JSON.

    :param value:
        A value to be decoded.
    :returns:
        The decoded value.
    """
    return decode(base64.b64decode(value))


def quote(value):
    """Serializes a value to JSON and encodes it using urllib.quote.

    :param value:
        A value to be encoded.
    :returns:
        The encoded value.
    """
    return urllib.quote(encode(value))


def unquote(value):
    """Decodes a value using urllib.unquote and deserializes it from JSON.

    :param value:
        A value to be decoded.
    :returns:
        The decoded value.
    """
    return decode(urllib.unquote(value))
