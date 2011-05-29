.. _guide.response:

Building a Response
===================
The request handler instance builds the response using its response property.
This is initialized to an empty `WebOb <http://pythonpaste.org/webob/>`_ ``Response``
object by the application.

The response object's out property is a file-like object that can be used for
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
