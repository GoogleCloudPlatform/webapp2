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


Common Request attributes
-------------------------
body
  A file-like object that gives the body of the request.
content_type
  Content-type of the request body.
method
  The HTTP method, e.g., 'GET' or 'POST'.
url
  Full URI, e.g., ``'http://localhost/blog/article?id=1'``.
scheme
  URI scheme, e.g., 'http' or 'https'.
host
  URI host, e.g., ``'localhost:80'``.
host_url
  URI host including scheme, e.g., ``'http://localhost'``.
path_url
  URI host including scheme and path, e.g., ``'http://localhost/blog/article'``.
path
  URI path, e.g., ``'/blog/article'``.
path_qs
  URI path including the query string, e.g., ``'/blog/article?id=1'``.
query_string
  Query string, e.g., ``id=1``.
headers
  A dictionary like object with request headers. Keys are case-insensitive.
GET
  A dictionary-like object with variables from the query string, as unicode.
str_GET
  A dictionary-like object with variables from the query string, as a string.
POST
  A dictionary-like object with variables from a POST form, as unicode.
str_POST
  A dictionary-like object with variables from a POST form, as a strings.
cookies
  A dictionary-like object with cookie values.


Extra attributes
----------------
The parameters from the matched :class:`webapp2.Route` are set as attributes
of the request object. They are ``request.route_args``, for positional
arguments, and ``request.route_kwargs``, for keyword arguments. The matched
route object is available as ``request.route``.

A reference to the active WSGI application is also set as an attribute of the
request. You can access it in ``request.app``.


Learn more about WebOb
----------------------
WebOb is an open source third-party library. See the
`WebOb <http://pythonpaste.org/webob/>`_ documentation for a detailed API
reference and examples.
