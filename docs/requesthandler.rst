The RequestHandler class
========================


Overriding ``__init__()``
-------------------------
If you want to override the :meth:`webapp2.RequestHandler.__init__` method,
you must call :meth:`webapp2.RequestHandler.initialize` at the beginning and
:meth:`webapp2.RequestHandler.dispatch` at the end of the method. This is
because in webapp2 the handler dispatches the requested method on construction.
If you call the parent class at the beginning of the method, any other
initializations you do after it will be lost because the requested method will
have been dispatched already.

Here's a correct way to override ``__init__()``::

    class MyHandler(webapp2.RequestHandler):
        def __init__(self, request, response):
            # Set self.request, self.response and self.app.
            self.initialize(request, response)

            # ... add your custom initializations here ...
            # ...

            # Dispatch the requested method.
            self.dispatch()


Overriding ``dispatch()``
-------------------------
One of the advantadges of webapp2 over webapp is that you can wrap the
dispatching process of :class:`webapp2.RequestHandler` to perform actions
before and/or after the requested method is dispatched. You can do this
overriding the :meth:`webapp2.RequestHandler.dispatch` method. This can be
useful, for example, to test if requirements were met before actually
dispatching the requested method, or to perform actions in the response object
after the method was dispatched. Here's an example::

    class MyHandler(webapp2.RequestHandler):
        def dispatch(self):
            # ... check if requirements were met ...
            # ...

            if requirements_were_met:
                # Parent class will call the method to be dispatched
                # -- get() or post() or etc.
                super(self.__class__, self).dispatch()
            else:
                self.abort(403)

In this case, if the requirements were not met, the method won't ever be
dispatched and a "403 Forbidden" response will be returned instead.

There are several possibilities to explore overriding ``dispatch()``, like
performing common checkings, setting common attributes or post-processing the
response.

