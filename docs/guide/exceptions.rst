.. _guide.exceptions:

Exception handling
==================
A good app is prepared even when something goes wrong: a service is down,
the application didn't expect a given input type or many other errors that
can happen in a web application. To react to these cases, we need a good
exception handling mechanism and prepare the app to catch exceptions for the
unexpected scenarios.


Exceptions in handlers
----------------------
Handlers can catch exceptions implementing the method
:meth:`webapp2.RequestHandler.handle_exception`. It is a good idea to define
a base class that catches generic exceptions, and if needed override
``handle_exception()`` in extended classes to set more specific responses.

Here we will define a exception handling function in a base class, and the real
app classes extend it::

    import logging

    import webapp2

    class BaseHandler(webapp2.RequestHandler):
        def handle_exception(self, exception, debug):
            # Log the error.
            logging.exception(exception)

            # Set a custom message.
            response.write('An error occurred.')

            # If the exception is a HTTPException, use its error code.
            # Otherwise use a generic 500 error code.
            if isinstance(exception, webapp2.HTTPException):
                response.set_status(exception.code)
            else:
                response.set_status(500)

    class HomeHandler(BaseHandler):
        def get(self):
            self.response.write('This is the HomeHandler.')

    class ProductListHandler(BaseHandler):
        def get(self):
            self.response.write('This is the ProductListHandler.')

If something unexpected happens during the ``HomeHandler`` or
``ProductListHandler`` lifetime, ``handle_exception()`` will catch it because
they extend a class that implements exception handling.

You can use exception handling to log errors and display custom messages
instead of a generic error. You could also render a template with a friendly
message, or return a JSON with an error code, depending on your app.


Exceptions in the WSGI app
--------------------------
Uncaught exceptions can also be handled by the WSGI application. The WSGI app
is a good place to handle '404 Not Found' or '500 Internal Server Error'
errors, since it serves as a last attempt to handle all uncaught exceptions,
including non-registered URI paths or unexpected application behavior.

We catch exceptions in the WSGI App using error handlers registered in
:attr:`webapp2.WSGIApplication.error_handlers`. This is a dictionary that
maps HTTP status codes to callables that will handle the corresponding error
code. If the exception is not an ``HTTPException``, the status code 500 is
used.

Here we set error handlers to handle "404 Not Found" and "500 Internal Server
Error"::

    def handle_404(request, response, exception):
        response.write('Oops! I could swear this page was here!')
        response.set_status(404)

    def handle_500(request, response, exception):
        response.write('A server error occurred!')
        response.set_status(500)

    app = webapp2.WSGIApplication([
        webapp2.Route('/', handler='handlers.HomeHandler', name='home')
    ])
    app.error_handlers[404] = handle_404
    app.error_handlers[500] = handle_500

The error handler can be a simple function that accepts
``(request, response, exception)`` as parameters, and is responsible for
identifying the exception type and setting the response status code.
