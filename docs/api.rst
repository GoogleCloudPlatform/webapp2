.. _contents:

API Reference
=============
.. module:: webapp2

.. contents:: Table of Contents
   :depth: 3
   :backlinks: none


WSGI App
--------
.. autoclass:: WSGIApplication
   :members: request_class, response_class, router_class, config_class,
             error_handlers, __init__, __call__, wsgi_app, handle_exception,
             url_for, get_config, run


Request Handlers
----------------
.. autoclass:: RequestHandler
   :members: __init__, __call__, abort, error, redirect, redirect_to, url_for,
             get_config, handle_exception


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


Configuration
-------------
.. autoclass:: Config
   :members: loaded, __init__, __setitem__, update, setdefault, get,
             load_and_get


Utilities
---------
These are some other utilities used internally that are also available for
general use.

.. autofunction:: abort
.. autofunction:: get_valid_methods
.. autofunction:: import_string
.. autofunction:: url_escape
.. autofunction:: url_unescape
.. autofunction:: to_utf8
.. autofunction:: to_unicode
.. autofunction:: urlunsplit


.. _Another Do-It-Yourself Framework: http://pythonpaste.org/webob/do-it-yourself.html
.. _Flask: http://flask.pocoo.org/
.. _Tornado: http://www.tornadoweb.org/
.. _Werkzeug: http://werkzeug.pocoo.org/
