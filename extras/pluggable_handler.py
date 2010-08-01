from webapp2 import RequestHandler, get_valid_methods


class PluggableRequestHandler(RequestHandler):
    #: A list of plugin instances. A plugin can implement two methods that
    #: are called before and after the current request method is executed,
    #: except if the chain is stopped.
    #:
    #: before_dispatch(handler)
    #:     Called before the requested method is executed. If returns False,
    #:     stops the plugin chain do not execute the requested method.
    #:
    #: after_dispatch(handler)
    #:     Called after the requested method is executed. If returns False,
    #:     stops the plugin chain. These are called in reverse order.
    plugins = []

    def __call__(self, _method, *args, **kwargs):
        """Dispatches the requested method. If plugins are set, executes
        ``before_dispatch()`` and ``after_dispatch()`` plugin hooks.

        :param _method:
            The method to be dispatched: the request method in lower case
            (e.g., 'get', 'post', 'head', 'put' etc).
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
            valid = ', '.join(get_valid_methods(self))
            self.abort(405, headers=[('Allow', valid)])

        if not self.plugins:
            # No plugins are set: just execute the method.
            return method(*args, **kwargs)

        # Execute before_dispatch plugins.
        for plugin in self.plugins:
            hook = getattr(plugin, 'before_dispatch', None)
            if hook:
                rv = hook(self)
                if rv is False:
                    break
        else:
            # Execute the requested method.
            method(*args, **kwargs)

        # Execute after_dispatch plugins.
        for plugin in reversed(self.plugins):
            hook = getattr(plugin, 'after_dispatch', None)
            if hook:
                rv = hook(self)
                if rv is False:
                    break
