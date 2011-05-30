.. _guide.response:

Building a Response
===================
The request handler instance builds the response using its response property.
This is initialized to an empty `WebOb <http://pythonpaste.org/webob/>`_
``Response`` object by the application.

The response object's acts as a file-like object that can be used for
writing the body of the response.:

    class MyHandler(webapp2.RequestHandler):
        def get(self):
            self.response.write("<html><body><p>Hi there!</p></body></html>")

The response buffers all output in memory, then sends the final output when
the handler exits. webapp2 does not support streaming data to the client.

The ``clear()`` method erases the contents of the output buffer, leaving it
empty.

If the data written to the output stream is a Unicode value, or if the
response includes a ``Content-Type`` header that ends with ``; charset=utf-8``,
webapp2 encodes the output as UTF-8. By default, the ``Content-Type`` header
is ``text/html; charset=utf-8``, including the encoding behavior. If the
``Content-Type`` is changed to have a different charset, webapp2 assumes the
output is a byte string to be sent verbatim.


Common Response attributes
--------------------------
status
  Status message, e.g., '404 Not Found'.
status_int
  Status code as an ``int``, e.g., 404.
body
  The contents of the response, as a string.
unicode_body
  The contents of the response, as a unicode.
headers
  A dictionary-like object with headers. Keys are case-insensitive. It supports
  multiple values for a key, but you must use
  ``response.headers.add(key, value)`` to add keys. To get all values, use
  ``response.headers.getall(key)``.
headerlist
  List of headers, as a list of tuples ``(header_name, value)``.
charset
  Character encoding.
content_type
  'Content-Type' value from the headers, e.g., ``'text/html'``.
content_type_params
  Dictionary of extra Content-type parameters, e.g., ``{'charset': 'utf8'}``.
location
  'Location' header variable, used for redirects.
etag
  'ETag' header variable. You can automatically generate an etag based on the
  response body calling ``response.md5_etag()``.

WebOb is an open source third-party library. See the
`WebOb <http://pythonpaste.org/webob/>`_ documentation for a detailed API
reference and examples.
