The RequestHandler class
========================


Overriding ``__init__()``
-------------------------
If you want to override the :class:`webapp2.RequestHandler.__init__` method,
you must take care to call the parent class only at the end of the method.
This is because in webapp2 the handler dispatches the requested method on
construction. If you call the parent class at the beginning of the method,
any other initializations you do after it will be lost because the requested
method will have been dispatched already.

Here's a correct way to override ``__init__()``::

    class MyHandler(webapp2.RequestHandler):
        def __init__(self, request, response):
            # ... add your custom initializations here ...
            # ...

            # Parent class will set basic attributes and call the method to be
            # dispatched -- get() or post() or etc.
            super(self.__class__, self).__init__(request, response)

If you need to access the current :class:`webapp2.WSGIApplication` instance on
``__init__()``, it is available as an attribute of request: use
``request.app``.


Overriding ``dispatch()``
-------------------------
One of the advantadges of webapp2 over webapp is that you can wrap the
dispatching process of :class:`webapp2.RequestHandler` to perform actions
before and/or after the requested method is dispatched. You can do this
overriding the :class:`webapp2.RequestHandler.dispatch` method. This can be
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

