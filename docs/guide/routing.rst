.. _guide.routing:

URI routing
===========
`URI routing` is the process of taking the requested URI and deciding which
application handler will handle the current request. For this, we initialize
the :class:`WSGIApplication` defining a list of `routes`: each `route`
analyses the current request URI and, if it matches certain criterias,
returns the handler and optional variables extracted from the URI.

webapp2 offers a powerful and extensible system to match and build URIs,
which is explained in details in this section.


Simple routes
-------------
The simplest form of URI route in webapp2 is a tuple ``(regex, handler)``,
where `regex` is a regular expression to match the requested URI path and
`handler` is a :class:`webapp2.RequestHandler` to handle the request.

.. note::
   This routing mechanism is fully compatible with App Engine's webapp
   framework.

A list of routes is registered in the WSGI application, which will try each
one in order until one matches, and then call the corresponding handler::

    app = webapp2.WSGIApplication([
        (r'/', HomeHandler),
        (r'/products', ProductListHandler),
        (r'/products/(\d+)', ProductHandler),
    ])

If no route matches, an ``HTTPException`` is raised with status code 404,
and the WSGI application can handle it accordingly (see
:ref:`guide.exceptions`).

The `regex` part is an ordinary regular expression (see the :py:mod:`re`
module) that can define groups inside parentheses. The matched group values are
passed to the handler as positional arguments. In the example above, the last
route defines a group, so the handler will receive the matched value when the
route matches (one or more digits in this case).

The `handler` part is a callable as explained in :ref:`guide.handlers`.
One additional feature compared to webapp is that the handler can also be
defined as a string in dotted notation to be lazily imported when needed.
This is useful to avoid loading all modules when the app is initialized: we
can define handlers in different modules without needing to import all of them
to initialize the app. This is not only convenient but also speeds up the
application startup.

Our previous example could be rewritten using strings instead of handler
classes and splitting our handlers in two files, ``handlers.py`` and
``products.py``::

    app = webapp2.WSGIApplication([
        (r'/', 'handlers.HomeHandler'),
        (r'/products', 'products.ProductListHandler'),
        (r'/products/(\d+)', 'products.ProductHandler'),
    ])

When one of these routes matches, the handler will be imported by the routing
system if needed.

Simple routes are easy to use and enough for a lot of cases but don't support
keyword arguments, URI building, domain and subdomain matching, automatic
redirection and other useful features. For this, webapp2 offers the extended
routing mechanism that we'll see next.


Extended routes
---------------
webapp2 introduces a routing mechanism that extends the webapp model to provide
additional features [...]

TBD


Domain and subdomain matching
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
TBD
