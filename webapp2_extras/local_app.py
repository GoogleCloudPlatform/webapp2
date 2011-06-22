# -*- coding: utf-8 -*-
"""
    webapp2_extras.local_app
    ~~~~~~~~~~~~~~~~~~~~~~~~

    This module implements a WSGIApplication adapted for threaded environments.

    :copyright: 2011 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
import webapp2

from webapp2_extras import local


_local = local.Local()
_app_class = webapp2.WSGIApplication
_app_class.app = _app_class.active_instance = _local('app')
_app_class.request = _local('request')


class WSGIApplication(_app_class):
    """A WSGIApplication for threaded environments.

    This allows webapp2 to be used in non-GAE servers.
    """

    def set_globals(self, app=None, request=None):
        """Registers the global variables for app and request.

        For threaded environments, they are assigned to a proxy object that
        returns app and request using thread-local.

        :param app:
            A :class:`webapp2.WSGIApplication` instance or None to remove it
            from the globals.
        :param request:
            A :class:`webapp2.Request` instance or None to remove it from
            the globals.
        """
        if app is None and request is None:
            _local.__release_local__()
        else:
            _local.app = app
            _local.request = request
