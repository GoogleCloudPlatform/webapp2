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
            valid = ', '.join(webapp2.get_valid_methods(self))
            self.abort(405, headers=[('Allow', valid)])

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


class extension(object):
    """A wrapper for ``RequestHandler`` extension classes. Extensions are
    instantiated when first called passing the handler instance as parameter,
    and other specialized parameters defined by the extension. The extension
    class can also be defined as a string. For example::

        from my.template.engine import Template

        def init_template_engine(app, engine):
            # Set some template globals, filters and so on.
            pass

        # Extension declared at module level.
        template = extension(Template, after_create_engine=init_template_engine)

        class MyHandler(RequestHandler):
            # Use the extension we declared in the module.
            template = template
            # Declare a new extension as a string to be lazily imported.
            auth = extension('my.module.Auth')

            def get(self):
                html = self.template.render('index.html', user=self.auth.user)

                # ...

    This has the same effect same as instantiating the extensions on
    ``RequestHandler.__init__``, with some advantages:

    - Extensions can be lazy. A base handler can setup several extensions but
      they are only imported and used by extended classes when accessed.
    - Extension setup can be done separately and reused, with automatic handler
      binding on use.
    - Changing or swapping extension setups is easier and done in one place.
    """
    def __init__(self, _callable, _name=None, _with_obj=True, *args,
        **kwargs):
        if callable(_callable):
            self._callable = _callable
            self.__name__ = _name or _callable.__name__
        else:
            self._callable = None
            self._callable_str = _callable
            self.__name__ = _name or _callable

        self._with_obj = _with_obj
        self._args = args
        self._kwargs = kwargs

    def __get__(self, obj, type=None):
        if obj is None:
            return self

        res = getattr(obj, self.__name__, webapp2.REQUIRED_VALUE)

        if res is webapp2.REQUIRED_VALUE:
            if self._callable is None:
                self._callable = webapp2.import_string(self._callable_str,
                    silent=True)
                if not self._callable:
                    raise ImportError('Extension %s could not be '
                        'imported.' % self._callable_str)

            if self._with_obj:
                # Pass the object as first argument.
                res = self._callable(obj, *self._args, **self._kwargs)
            else:
                res = self._callable(*self._args, **self._kwargs)

            setattr(obj, self.__name__, res)

        return res
