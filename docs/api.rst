.. _contents:

webapp2
=======
.. module:: webapp2

.. contents:: Table of Contents
   :depth: 3
   :backlinks: none


WSGI App
--------
.. autoclass:: WSGIApplication
   :members: request_class, response_class, router_class, __init__, __call__,
             dispatch, handle_exception, url_for, run


.. autofunction:: get_app

.. autofunction:: get_request


Request Handlers
----------------
.. autoclass:: RequestHandler
   :members: __init__, __call__, abort, error, redirect, redirect_to, url_for,
             handle_exception, get_valid_methods


.. autoclass:: RedirectHandler
   :members: get


URL Routing
-----------
.. autoclass:: Router
   :members: route_class, __init__, add, build, match, dispatch

.. autoclass:: BaseRoute
   :members: name, build_only, match, build, get_routes, get_match_routes,
             get_build_routes

.. autoclass:: SimpleRoute
   :members: __init__, match

.. autoclass:: Route
   :members: __init__, match, build


Utilities
---------
These are some other utilities used internally that are also available for
general use.

.. autoclass:: cached_property

.. autofunction:: abort

.. autofunction:: import_string

.. autofunction:: to_utf8

.. autofunction:: to_unicode

.. autofunction:: urlunsplit


.. _Another Do-It-Yourself Framework: http://pythonpaste.org/webob/do-it-yourself.html
.. _Flask: http://flask.pocoo.org/
.. _Tornado: http://www.tornadoweb.org/
.. _Werkzeug: http://werkzeug.pocoo.org/
