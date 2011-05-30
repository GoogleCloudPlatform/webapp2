.. _guide.testing:

Unit testing
============
Thanks to `WebOb <http://pythonpaste.org/webob/>`_, webapp2 is very testable.
Testing a handler is a matter of building a custom ``Request`` object and
calling ``get_response()`` on it passing the WSGI application.

Let's see an example. First define a simple 'Hello world' handler to be
tested::

    import webapp2

    class HelloHandler(webapp2.RequestHandler):
        def get(self):
            self.response.write('Hello, world!')

    app = webapp2.WSGIapplication([('/', HelloHandler)])

    def main():
        app.run()

    if __name__ == '__main__':
        main()

To test if this handler returns the correct ``'Hello, world!'`` response, we
build a request object using ``Request.blank()`` and call ``get_response()``
on it::

    import unittest
    import webapp2

    # from the app main.py
    import main

    class TestHandlers(unittest.TestCase):
       def test_hello(self):
           # Build a request object passing the URI path to be tested.
           # You can also pass headers, query arguments etc.
           request = webapp2.Request.blank('/')
           # Get a response for that request.
           response = request.get_response(main.app)

           # Let's check if the response is correct.
           self.assertEqual(response.status, '200 OK')
           self.assertEqual(response.body, 'Hello, world!')

To test different HTTP methods, just change the request object::

    request = webapp2.Request.blank('/')
    request.method = 'POST'
    response = request.get_response(main.app)

    # Our handler doesn't implement post(), so this response will have a
    # status code 405.
    self.assertEqual(response.status, '405 Method Not Allowed')


app.get_response()
------------------
We can also get a response directly from the WSGI application, calling
``app.get_response()``. This is a convenience for unit testing purposes.
It receives the same parameters as ``Request.blank()`` to build a request
and calls the application, returning the resulting response::

    class HelloHandler(webapp2.RequestHandler):
        def get(self):
            self.response.write('Hello, world!')

    app = webapp2.WSGIapplication([('/', HelloHandler)])

    # Test the app, passing parameters to build a request.
    response = app.get_response('/')
    assert response.status == '200 OK'
    assert response.body == 'Hello, world!'

Testing handlers could not be easier. Check the
`WebOb <http://pythonpaste.org/webob/#methods>`_ documentation for more
information about the ``Request.blank()`` parameters.
