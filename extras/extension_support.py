# -*- coding: utf-8 -*-
"""
    Plugin extension
    ~~~~~~~~~~~~~~~~

    Extends ``RequestHandler``, ``Request`` and ``WSGIApplication`` to
    add minimal infra-structure for plugins and extensions:

    - ``RequestHandler`` dispatch hooks.
    - ``Request`` registry and context.
    - ``WSGIApplication`` registry.
"""
import webapp2


class RequestHandler(webapp2.RequestHandler):
    #: A list of plugin instances. A plugin can implement two methods that
    #: are called before and after the current request method is executed,
    #: except if the chain is stopped.
    #:
    #: before_dispatch(handler)
    #:     Called before the requested method is executed. If returns True,
    #:     stops the plugin chain and doesn't execute the requested method.
    #:
    #: after_dispatch(handler)
    #:     Called after the requested method is executed. If returns True,
    #:     stops the plugin chain. These are called in reverse order.
    plugins = []

    def __call__(self, _method, *args, **kwargs):
        """Dispatches the requested method.

        :param _method:
            The method to be dispatched: the request method in lower case
            (e.g., 'get', 'post', 'head', 'put' etc).
        :param args:
            Positional arguments to be passed to the method, coming from the
            matched :class:`Route`.
        :param kwargs:
            Keyword arguments to be passed to the method, coming from the
            matched :class:`Route`.
        :returns:
            None.
        """
        method = getattr(self, _method, None)
        if method is None:
            # 405 Method Not Allowed.
            # The response MUST include an Allow header containing a
            # list of valid methods for the requested resource.
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.6
            valid = ', '.join(webapp2.get_valid_methods(self))
            self.abort(405, headers=[('Allow', valid)])

        if not self.plugins:
            # Simply execute the requested method.
            return method(*args, **kwargs)

        # Execute before_dispatch plugins.
        for plugin in self.plugins:
            hook = getattr(plugin, 'before_dispatch', None)
            if hook and hook(self) is True:
                break
        else:
            # Execute the requested method.
            method(*args, **kwargs)

        # Execute after_dispatch plugins.
        for plugin in reversed(self.plugins):
            hook = getattr(plugin, 'after_dispatch', None)
            if hook and hook(self) is True:
                break


class Request(webapp2.Request):
    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        # A registry for objects in use during a request.
        self.registry = {}
        # A context for template variables.
        self.context = {}


class WSGIApplication(webapp2.WSGIApplication):
    #: Default class used for the request object.
    request_class = Request

    def __init__(self, *args, **kwargs):
        super(WSGIApplication, self).__init__(*args, **kwargs)
        # A registry for objects instantiated for this app.
        self.registry = {}
