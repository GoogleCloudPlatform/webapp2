.. _contents:

webapp2
=======
.. module:: webapp2


WSGI app
--------
.. autoclass:: WSGIApplication
   :members: request_class, response_class, router_class, request_context_class,
             debug, router, registry, error_handlers, app, request,
             active_instance, allowed_methods,
             __init__, __call__, set_globals, handle_exception, run,
             get_response


Request handlers
----------------
.. autoclass:: RequestHandler
   :members: app, request, response, __init__, initialize, dispatch, error,
             abort, redirect, redirect_to, uri_for, handle_exception,
             factory


.. autoclass:: RedirectHandler
   :members: get


URI routing
-----------
.. autoclass:: Router
   :members: route_class, __init__, add, set_matcher, set_dispatcher,
             set_builder, default_matcher, default_dispatcher, default_builder,
             build, match, dispatch

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

.. autofunction:: get_app

.. autofunction:: get_request

.. autofunction:: abort

.. autofunction:: import_string

.. autofunction:: urlunsplit


.. _Another Do-It-Yourself Framework: http://pythonpaste.org/webob/do-it-yourself.html
.. _Flask: http://flask.pocoo.org/
.. _Tornado: http://www.tornadoweb.org/
.. _Werkzeug: http://werkzeug.pocoo.org/
