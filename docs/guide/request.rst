.. _guide.request:

Request data
============
The request handler instance can access the request data using its ``request``
property. This is initialized to a populated `WebOb <http://pythonpaste.org/webob/>`_
``Request`` object by the application.

The request object provides a ``get()`` method that returns values for
arguments parsed from the query and from POST data. The method takes the
argument name as its first parameter. For example::

    class MyHandler(webapp2.RequestHandler):
        def post(self):
            name = self.request.get('name')

By default, ``get()`` returns the empty string (``''``) if the requested
argument is not in the request. If the parameter ``default_value`` is
specified, ``get()`` returns the value of that parameter instead of the empty
string if the argument is not present.

If the argument appears more than once in a request, by default ``get()``
returns the first occurrence. To get all occurrences of an argument that might
appear more than once as a list (possibly empty), give ``get()`` the argument
``allow_multiple=True``::

    # <input name="name" type="text" />
    name = self.request.get("name")

    # <input name="subscribe" type="checkbox" value="yes" />
    subscribe_to_newsletter = self.request.get("subscribe", default_value="no")

    # <select name="favorite_foods" multiple="true">...</select>
    favorite_foods = self.request.get("favorite_foods", allow_multiple=True)
    for food in favorite_foods:
    # ...

For requests with body content that is not a set of CGI parameters, such as
the body of an HTTP PUT request, the request object provides the attributes
``body`` and ``body_file``: ``body`` is the body content as a byte string and
``body_file`` provides a file-like interface to the same data::

    uploaded_file = self.request.body

WebOb is an open source third-party library. See the `WebOb <http://pythonpaste.org/webob/>`_
documentation for a detailed API reference and examples.
