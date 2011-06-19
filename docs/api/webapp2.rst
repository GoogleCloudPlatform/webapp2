.. _Another Do-It-Yourself Framework: http://pythonpaste.org/webob/do-it-yourself.html
.. _Flask: http://flask.pocoo.org/
.. _Tornado: http://www.tornadoweb.org/
.. _WebOb: http://pythonpaste.org/webob/
.. _Werkzeug: http://werkzeug.pocoo.org/

.. _contents:

webapp2
=======
.. module:: webapp2

- WSGI app

  - :class:`WSGIApplication`
  - :class:`RequestContext`

- Configuration

  - :class:`Config`

- Request and Response

  - :class:`Request`
  - :class:`Response`

- Request handlers

  - :class:`RequestHandler`
  - :class:`RedirectHandler`

- URI routing

  - :class:`Router`
  - :class:`BaseRoute`
  - :class:`SimpleRoute`
  - :class:`Route`

- Utilities

  - :class:`cached_property`
  - :func:`get_app`
  - :func:`get_request`
  - :func:`redirect`
  - :func:`uri_for`
  - :func:`abort`
  - :func:`import_string`
  - :func:`urlunsplit`


WSGI app
--------
.. seealso::
   :ref:`guide.app`

.. autoclass:: WSGIApplication
   :members: request_class, response_class, request_context_class,
             router_class, config_class,
             debug, router, config, registry, error_handlers, app, request,
             active_instance, allowed_methods,
             __init__, __call__, set_globals, handle_exception, run,
             get_response

.. autoclass:: RequestContext
   :members: __init__, __enter__, __exit__


Configuration
-------------
.. seealso::
   :ref:`guide.app.config`

.. autoclass:: Config
   :members: __init__, load_config


Request and Response
--------------------
.. seealso::
   :ref:`guide.request` and :ref:`guide.response`

.. autoclass:: Request
   :members: app, response, route, route_args, route_kwargs, registry
             __init__, get, get_all, arguments, get_range,


.. autoclass:: Response
   :members: __init__, status, status_message, has_error, clear, wsgi_write,
             http_status_message


Request handlers
----------------
.. seealso::
   :ref:`guide.handlers`

.. autoclass:: RequestHandler
   :members: app, request, response, __init__, initialize, dispatch, error,
             abort, redirect, redirect_to, uri_for, handle_exception,
             factory


.. autoclass:: RedirectHandler
   :members: get


URI routing
-----------
.. seealso::
   :ref:`guide.app.router` and :ref:`guide.routing`

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

.. autofunction:: redirect

.. autofunction:: uri_for

.. autofunction:: abort

.. autofunction:: import_string

.. autofunction:: urlunsplit
