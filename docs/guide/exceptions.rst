.. _guide.exceptions:

Exception handling
==================
Uncaught exceptions can also be handled by the WSGI application, using error
handlers registered in :attr:`WSGIApplication.error_handlers`. This is a
dictionary that maps HTTP status codes to callables that will handle the
corresponding error code. If the exception is not an ``HTTPException``, the
status code 500 is used.

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

