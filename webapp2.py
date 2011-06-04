# -*- coding: utf-8 -*-
"""
    webapp2
    =======

    Taking Google App Engine's webapp to the next level!

    :copyright: 2011 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
from __future__ import with_statement

import logging
import re
import urllib
import urlparse

import webob
from webob import exc

try:
    from google.appengine.ext import webapp
    from google.appengine.ext.webapp import util
except ImportError:
    # Allow running webapp2 outside of GAE.
    from wsgiref import handlers

    class webapp(object):
        Request = webob.Request
        RequestHandler = type('RequestHandler', (object,), {})

    class util(object):
        def _run(self, app):
            handlers.CGIHandler().run(app)

        run_bare_wsgi_app = classmethod(_run)
        run_wsgi_app = classmethod(_run)

__version_info__ = ('1', '7')
__version__ = '.'.join(__version_info__)

#: Base HTTP exception, set here as public interface.
HTTPException = exc.HTTPException

#: Regex for URI definitions.
_ROUTE_REGEX = re.compile(r"""
    \<               # The exact character "<"
    (\w+)?           # The optional variable name ([a-zA-Z0-9_]+)
    (?::([^>]*))?    # The optional :regex part
    \>               # The exact character ">"
    """, re.VERBOSE)


class Request(webapp.Request):
    """Abstraction for an HTTP request."""

    #: A reference to the active :class:`WSGIApplication` instance.
    app = None
    #: A reference to the active :class:`Response` instance.
    response = None
    #: A reference to the matched :class:`Route`.
    route = None
    #: The matched route positional arguments.
    route_args = None
    #: The matched route keyword arguments.
    route_kwargs = None
    #: A dictionary to register objects used during the request lifetime.
    registry = None

    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        self.registry = {}


class Response(webob.Response):
    """Abstraction for an HTTP response.

    Implements most of ``webapp.Response`` interface, except ``wsgi_write()``
    as the response itself is returned by the WSGI application.
    """

    default_content_type = 'text/html'
    default_charset = 'utf-8'

    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args, **kwargs)
        # webapp uses response.out.write(), so we point `.out` to `self`
        # and it will use `Response.write()`.
        self.out = self

    def write(self, text):
        """Appends a text to the response body."""
        # webapp uses StringIO as Response.out, so we need to convert anything
        # that is not str or unicode to string to keep same behavior.
        if not isinstance(text, basestring):
            text = unicode(text)

        if isinstance(text, unicode) and not self.charset:
            self.charset = self.default_charset

        super(Response, self).write(text)

    def set_status(self, code, message=None):
        """Sets the HTTP status code of this response.

        :param code:
            The HTTP status string to use
        :param message:
            A status string. If none is given, uses the default from the
            HTTP/1.1 specification.
        """
        if message:
            self.status = '%d %s' % (code, message)
        else:
            self.status = code

    def clear(self):
        """Clears all data written to the output stream so that it is empty."""
        self.body = ''

    @staticmethod
    def http_status_message(code):
        """Returns the default HTTP status message for the given code.

        :param code:
            The HTTP code for which we want a message.
        """
        message = webob.statusreasons.status_reasons.get(code)
        if not message:
            raise KeyError('Invalid HTTP status code: %d' % code)

        return message


class RequestHandler(object):
    """Base HTTP request handler.

    Implements most of ``webapp.RequestHandler`` interface.
    """

    #: A :class:`Request` instance.
    request = None
    #: A :class:`Response` instance.
    response = None
    #: A :class:`WSGIApplication` instance.
    app = None

    def __init__(self, request=None, response=None):
        """Initializes this request handler with the given WSGI application,
        Request and Response.

        When instantiated by ``webapp.WSGIApplication``, request and response
        are not set on instantiation. Instead, initialize() is called right
        after the handler is created to set them.

        Also in webapp dispatching is done by the WSGI app, while webapp2
        does it here to allow more flexibility in extended classes: handlers
        can wrap :meth:`dispatch` to check for conditions before executing the
        requested method and/or post-process the response.

        .. note::
           Parameters are optional only to support webapp's constructor which
           doesn't take any arguments. Consider them as required.

        :param request:
            A :class:`Request` instance.
        :param response:
            A :class:`Response` instance.
        """
        self.initialize(request, response)

    def initialize(self, request, response):
        """Initializes this request handler with the given WSGI application,
        Request and Response.

        :param request:
            A :class:`Request` instance.
        :param response:
            A :class:`Response` instance.
        """
        self.request = request
        self.response = response
        self.app = WSGIApplication.active_instance

    def dispatch(self):
        """Dispatches the request.

        This will first check if there's a handler_method defined in the
        matched route, and if not it'll use the method correspondent to the
        request method (``get()``, ``post()`` etc).
        """
        request = self.request
        method_name = request.route.handler_method
        if not method_name:
            method_name = _normalize_handler_method(request.method)

        method = getattr(self, method_name, None)
        if method is None:
            # 405 Method Not Allowed.
            # The response MUST include an Allow header containing a
            # list of valid methods for the requested resource.
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.6
            valid = ', '.join(_get_handler_methods(self))
            self.abort(405, headers=[('Allow', valid)])

        # The handler only receives *args if no named variables are set.
        args, kwargs = request.route_args, request.route_kwargs
        if kwargs:
            args = ()

        try:
            return method(*args, **kwargs)
        except Exception, e:
            return self.handle_exception(e, self.app.debug)

    def error(self, code):
        """Clears the response and sets the given HTTP status code.

        This doesn't stop code execution; for this, use :meth:`abort`.

        :param code:
            HTTP status error code (e.g., 501).
        """
        self.response.set_status(code)
        self.response.clear()

    def abort(self, code, *args, **kwargs):
        """Raises an :class:`HTTPException`.

        This stops code execution, leaving the HTTP exception to be handled
        by an exception handler.

        :param code:
            HTTP status code (e.g., 404).
        :param args:
            Positional arguments to be passed to the exception class.
        :param kwargs:
            Keyword arguments to be passed to the exception class.
        """
        abort(code, *args, **kwargs)

    def redirect(self, uri, permanent=False, abort=False, code=None):
        """Issues an HTTP redirect to the given relative URI.

        This won't stop code execution unless **abort** is True. A common
        practice is to return when calling this method::

            return self.redirect('/some-path')

        :param uri:
            A relative or absolute URI (e.g., ``'../flowers.html'``).
        :param permanent:
            If True, uses a 301 redirect instead of a 302 redirect.
        :param abort:
            If True, raises an exception to perform the redirect.
        :param code:
            The redirect status code. Supported codes are 301, 302, 303, 305,
            and 307.  300 is not supported because it's not a real redirect
            and 304 because it's the answer for a request with defined
            ``If-Modified-Since`` headers.

        .. seealso:: :meth:`redirect_to`.
        """
        if uri.startswith(('.', '/')):
            uri = str(urlparse.urljoin(self.request.url, uri))

        if code is None:
            if permanent:
                code = 301
            else:
                code = 302

        assert code in (301, 302, 303, 305, 307), \
            'Invalid redirect status code.'

        if abort:
            self.abort(code, headers=[('Location', uri)])

        self.response.headers['Location'] = uri
        self.response.set_status(code)
        self.response.clear()

    def redirect_to(self, _name, _permanent=False, _abort=False, _code=None,
        *args, **kwargs):
        """Convenience method mixing :meth:`redirect` and :meth:`uri_for`.

        Issues an HTTP redirect to a named URI built using :meth:`uri_for`.

        :param _name:
            The route name to redirect to.
        :param args:
            Positional arguments to build the URI.
        :param kwargs:
            Keyword arguments to build the URI.

        The other arguments are described in :meth:`redirect`.
        """
        url = self.uri_for(_name, *args, **kwargs)
        self.redirect(url, permanent=_permanent, abort=_abort, code=_code)

    def uri_for(self, _name, *args, **kwargs):
        """Returns a URI for a named :class:`Route`.

        .. seealso:: :meth:`Router.build`.
        """
        return self.app.router.build(self.request, _name, args, kwargs)
    # Alias.
    url_for = uri_for

    def handle_exception(self, exception, debug):
        """Called if this handler throws an exception during execution.

        The default behavior is to re-raise the exception to be handled by
        :meth:`WSGIApplication.handle_exception`.

        :param exception:
            The exception that was thrown.
        :param debug_mode:
            True if the web application is running in debug mode.
        """
        raise

    @classmethod
    def factory(cls, request, response):
        """Constructs an instance and dispatches this handler."""
        handler = cls(request, response)
        return handler.dispatch()


class RedirectHandler(RequestHandler):
    """Redirects to the given URI for all GET requests.

    This is intended to be used when defining URI routes. You must provide at
    least the keyword argument *url* in the route default values. Example::

        def get_redirect_url(handler, *args, **kwargs):
            return handler.uri_for('new-route-name')

        app = WSGIApplication([
            Route('/old-url', RedirectHandler, defaults={'_uri': '/new-url'}),
            Route('/other-old-url', RedirectHandler, defaults={'_uri': get_redirect_url}),
        ])

    Based on idea from `Tornado`_.
    """

    def get(self, *args, **kwargs):
        """Performs a redirect.

        Two keyword arguments can be passed through the URI route:

        - **_uri**: A URI string or a callable that returns a URI. The callable
          is called passing ``(handler, *args, **kwargs)`` as arguments.
        - **_code**: The redirect status code. Default is 301 (permanent
          redirect).
        """
        uri = kwargs.pop('_uri', '/')
        permanent = kwargs.pop('_permanent', True)
        code = kwargs.pop('_code', None)

        func = getattr(uri, '__call__', None)
        if func:
            uri = func(self, *args, **kwargs)

        self.redirect(uri, permanent=permanent, code=code)


class cached_property(object):
    """A decorator that converts a function into a lazy property.

    The function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value::

        class Foo(object):

            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a `__dict__` in order for this property to
    work.

    .. note:: Implementation detail: this property is implemented as non-data
       descriptor.  non-data descriptors are only invoked if there is
       no entry with the same name in the instance's __dict__.
       this allows us to completely get rid of the access function call
       overhead.  If one choses to invoke __get__ by hand the property
       will still work as expected because the lookup logic is replicated
       in __get__ for manual invocation.

    This class comes from `Werkzeug`_.
    """

    _default_value = object()

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self

        value = obj.__dict__.get(self.__name__, self._default_value)
        if value is self._default_value:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value

        return value


class BaseRoute(object):
    """Interface for URI routes."""

    #: The regex template.
    template = None
    #: Route name, used to build URIs.
    name = None
    #: True if this route is only used for URI generation and never matches.
    build_only = False
    #: The handler or string or in dotted notation to be lazily imported.
    handler = None
    #: The custom handler method, if handler is a class.
    handler_method = None

    def match(self, request):
        """Matches all routes against a request object.

        The first one that matches is returned.

        :param request:
            A :class:`Request` instance.
        :returns:
            A tuple ``(route, args, kwargs)`` if a route matched, or None.
        """
        raise NotImplementedError()

    def build(self, request, args, kwargs):
        """Returns a URI for this route.

        :param request:
            The current :class:`Request` object.
        :param args:
            Tuple of positional arguments to build the URI.
        :param kwargs:
            Dictionary of keyword arguments to build the URI.
        :returns:
            An absolute or relative URI.
        """
        raise NotImplementedError()

    def get_routes(self):
        """Generator to get all routes from a route.

        :yields:
            This route or all nested routes that it contains.
        """
        yield self

    def get_match_routes(self):
        """Generator to get all routes that can be matched from a route.

        :yields:
            This route or all nested routes that can be matched.
        """
        if not self.build_only:
            yield self
        elif not self.name:
            raise ValueError(
                "Route %r is build_only but doesn't have a name." % self)

    def get_build_routes(self):
        """Generator to get all routes that can be built from a route.

        :yields:
            This route or all nested routes that can be built.
        """
        if self.name is not None:
            yield self


class SimpleRoute(BaseRoute):
    """A route that is compatible with webapp's routing mechanism.

    URI building is not implemented as webapp has rudimentar support for it,
    and this is the most unknown webapp feature anyway.
    """

    def __init__(self, template, handler):
        """Initializes this route.

        :param template:
            A regex to be matched.
        :param handler:
            A callable or string in dotted notation to be lazily imported,
            e.g., ``'my.module.MyHandler'`` or ``'my.module.my_function'``.
            The callable is called passing (request, response) as arguments.
        """
        self.template = template
        self.handler = handler

    @cached_property
    def regex(self):
        """Lazy regex compiler."""
        if not self.template.startswith('^'):
            self.template = '^' + self.template

        if not self.template.endswith('$'):
            self.template += '$'

        return re.compile(self.template)

    def match(self, request):
        """Matches this route against the current request.

        .. seealso:: :meth:`BaseRoute.match`.
        """
        match = self.regex.match(request.path)
        if match:
            return self, match.groups(), {}

    def __repr__(self):
        return '<SimpleRoute(%r, %r)>' % (self.template, self.handler)


class Route(BaseRoute):
    """A route definition that maps a URI path to a handler.

    The initial concept was based on `Another Do-It-Yourself Framework`_, by
    Ian Bicking.
    """

    #: Name of the method to be used, if handler is a class.
    handler_method = None
    #: Default parameters values.
    defaults = None
    #: Sequence of allowed HTTP methods. If not set, all methods are allowed.
    methods = None
    # Lazy properties extracted from the route template.
    regex = None
    reverse_template = None
    variables = None
    args_count = 0
    kwargs_count = 0

    def __init__(self, template, handler=None, name=None, defaults=None,
        build_only=False, handler_method=None, methods=None):
        """Initializes this route.

        :param template:
            A route template to match against the request path. A template
            can have variables enclosed by ``<>`` that define a name, a
            regular expression or both. Examples:

              =================  ==================================
              Format             Example
              =================  ==================================
              ``<name>``         ``'/blog/<year>/<month>'``
              ``<:regex>``       ``'/blog/<:\d{4}>/<:\d{2}>'``
              ``<name:regex>``   ``'/blog/<year:\d{4}>/<month:\d{2}>'``
              =================  ==================================

            The same template can mix parts with name, regular expression or
            both.

            If the name is set, the value of the matched regular expression
            is passed as keyword argument to the handler. Otherwise it is
            passed as positional argument.

            If only the name is set, it will match anything except a slash.
            So these routes are equivalent::

                Route('/<user_id>/settings', handler=SettingsHandler, name='user-settings')
                Route('/<user_id:[^/]+>/settings', handler=SettingsHandler, name='user-settings')

            .. note::
               The handler only receives ``*args`` if no named variables are
               set. Otherwise, the handler only receives ``**kwargs``. This
               allows you to set regular expressions that are not captured:
               just mix named and unnamed variables and the handler will
               only receive the named ones.

        :param handler:
            A callable or string in dotted notation to be lazily imported,
            e.g., ``'my.module.MyHandler'`` or ``'my.module.my_function'``.
            The callable is called passing (request, response) as arguments.
            It is possible to define a method if the callable is a class,
            separating it by a colon: ``'my.module.MyHandler:my_method'``.
            This is a shortcut and has the same effect as defining the
            `handler_method` parameter.
        :param name:
            The name of this route, used to build URIs based on it.
        :param defaults:
            Default or extra keywords to be returned by this route. Values
            also present in the route variables are used to build the URI
            when they are missing.
        :param build_only:
            If True, this route never matches and is used only to build URIs.
        :param handler_method:
            The name of a custom handler method to be called, in case `handler`
            is a class. If not defined, the default behavior is to call the
            handler method correspondent to the HTTP request method in lower
            case (e.g., `get()`, `post()` etc).
        :param methods:
            A sequence of HTTP methods. If set, the route will only match if
            the request method is allowed.
        """
        self.template = template
        self.handler = handler
        self.name = name
        self.defaults = defaults or {}
        self.build_only = build_only
        self.methods = methods
        # If a handler string has a colon, we take it as the method from a
        # handler class, e.g., 'my_module.MyClass:my_method', and store it
        # in the route as 'handler_method'. Not every route mapping to a class
        # must define a method (the request method is used by default), and for
        # functions 'handler_method' is of course always None.
        self.handler_method = handler_method
        if isinstance(handler, basestring) and handler.rfind(':') != -1:
            if handler_method:
                raise ValueError(
                    "If handler_method is defined in a Route, handler "
                    "can't have a colon (got %r)." % handler)
            else:
                self.handler, self.handler_method = handler.rsplit(':', 1)

    @cached_property
    def regex(self):
        """Lazy regex template parser."""
        self.variables = {}
        self.reverse_template = pattern = ''
        self.args_count = last = 0
        for match in _ROUTE_REGEX.finditer(self.template):
            part = self.template[last:match.start()]
            name = match.group(1)
            expr = match.group(2) or '[^/]+'
            last = match.end()

            if not name:
                name = '__%d__' % self.args_count
                self.args_count += 1

            pattern += '%s(?P<%s>%s)' % (re.escape(part), name, expr)
            self.reverse_template += '%s%%(%s)s' % (part, name)
            self.variables[name] = re.compile('^%s$' % expr)

        part = self.template[last:]
        self.kwargs_count = len(self.variables) - self.args_count
        self.reverse_template += part
        return re.compile('^%s%s$' % (pattern, re.escape(part)))

    def match(self, request):
        """Matches this route against the current request.

        :raises:
            ``exc.HTTPMethodNotAllowed`` if the route defines :attr:`methods`
            and the request method isn't allowed.

        .. seealso:: :meth:`BaseRoute.match`.
        """
        match = self.regex.match(request.path)
        if not match:
            return None

        if self.methods and request.method not in self.methods:
            # Is this a good idea? What if other route is set for this path
            # but different HTTP method?
            raise exc.HTTPMethodNotAllowed()

        kwargs = self.defaults.copy()
        kwargs.update(match.groupdict())
        if kwargs and self.args_count:
            args = tuple(value[1] for value in sorted(
                (int(key[2:-2]), kwargs.pop(key)) for key in kwargs.keys() \
                if key.startswith('__') and key.endswith('__')))
        else:
            args = ()

        return self, args, kwargs

    def build(self, request, args, kwargs):
        """Returns a URI for this route.

        .. seealso:: :meth:`Router.build`.
        """
        scheme = kwargs.pop('_scheme', None)
        netloc = kwargs.pop('_netloc', None)
        anchor = kwargs.pop('_fragment', kwargs.pop('_anchor', None))
        full = kwargs.pop('_full', False) and not scheme and not netloc

        if full or scheme or netloc:
            netloc = netloc or request.host
            scheme = scheme or request.scheme

        path, query = self._build(args, kwargs)
        return urlunsplit(scheme, netloc, path, query, anchor)

    def _build(self, args, kwargs):
        """Returns the URI path for this route.

        :returns:
            A tuple ``(path, kwargs)`` with the built URI path and extra
            keywords to be used as URI query arguments.
        """
        # Access self.regex just to set the lazy properties.
        regex = self.regex
        variables = self.variables
        if self.args_count:
            for index, value in enumerate(args):
                key = '__%d__' % index
                if key in variables:
                    kwargs[key] = value

        values = {}
        for name, regex in variables.iteritems():
            value = kwargs.pop(name, self.defaults.get(name))
            if not value:
                raise KeyError('Missing argument "%s" to build URI.' % \
                    name.strip('_'))

            if not isinstance(value, basestring):
                value = str(value)

            if not regex.match(value):
                raise ValueError('URI buiding error: Value "%s" is not '
                    'supported for argument "%s".' % (value, name.strip('_')))

            values[name] = value

        return (self.reverse_template % values, kwargs)

    def __repr__(self):
        return '<Route(%r, %r, name=%r, defaults=%r, build_only=%r)>' % \
            (self.template, self.handler, self.name, self.defaults,
            self.build_only)


class Router(object):
    """A URI router used to match, dispatch and build URIs."""

    #: Class used when the route is a tuple, for compatibility with webapp.
    route_class = SimpleRoute
    #: Function to match a request. Default is :meth:`default_matcher`.
    match = None
    #: Function to dispatch a request. Default is :meth:`default_dispatcher`.
    dispatch = None
    #: Function to build a URI. Default is :meth:`default_builder`.
    build = None
    #: Several internal attributes.
    app = None
    match_routes = None
    build_routes = None
    _handlers = None

    def __init__(self, routes=None):
        """Initializes the router.

        :param routes:
            A list of :class:`Route` instances. For compatibility with webapp,
            the list items can also be a tuple ``(regex, handler_class)``.
        """
        # Default dispatcher, matcher and builder.
        self.match = self.default_matcher
        self.dispatch = self.default_dispatcher
        self.build = self.default_builder
        # Handler classes imported lazily.
        self._handlers = {}
        # All routes that can be matched.
        self.match_routes = []
        # All routes that can be built.
        self.build_routes = {}
        if routes:
            for route in routes:
                self.add(route)

    def add(self, route):
        """Adds a route to this router.

        :param route:
            A :class:`Route` instance.
        """
        if isinstance(route, tuple):
            # Exceptional compatibility case: route compatible with webapp.
            route = self.route_class(*route)

        for r in route.get_match_routes():
            self.match_routes.append(r)

        for r in route.get_build_routes():
            self.build_routes[r.name] = r

    def set_matcher(self, func):
        """Sets the function called to match URIs.

        :param func:
            A function that receives ``(router, request)`` and returns
            a tuple ``(route, args, kwargs)``  if any route matches.
        """
        self.match = lambda *args, **kwargs: func(self, *args, **kwargs)

    def default_matcher(self, request):
        """Matches all routes against a request object.

        The first one that matches is returned.

        :param request:
            A :class:`Request` instance.
        :returns:
            A tuple ``(route, args, kwargs)`` if a route matched, or None.
        :raises:
            ``exc.HTTPNotFound`` if no route matched.
        """
        for route in self.match_routes:
            match = route.match(request)
            if match:
                return match

        raise exc.HTTPNotFound()

    def set_dispatcher(self, func):
        """Sets the function called for dispatch the handler.

        :param func:
            A function that receives ``(router, request, response)``
            and returns the value returned by the dispatched handler.
        """
        self.dispatch = lambda *args, **kwargs: func(self, *args, **kwargs)

    def default_dispatcher(self, request, response):
        """Dispatches a handler.

        :param request:
            A :class:`Request` instance.
        :param response:
            A :class:`Response` instance.
        :raises:
            ``exc.HTTPNotFound`` if no route matched.
        :returns:
            The returned value from the handler.
        """
        request.route, request.route_args, request.route_kwargs = \
            self.match(request)
        handler = request.route.handler
        if isinstance(handler, basestring):
            if handler not in self._handlers:
                self._handlers[handler] = import_string(handler)

            request.route.handler = handler = self._handlers[handler]

        # The handler can provide a factory method, or we will monkeypatch
        # it to do so.
        factory = getattr(handler, 'factory', None)
        if not factory:
            try:
                if issubclass(handler, webapp.RequestHandler):
                    # Compatible with webapp.RequestHandler.
                    handler.factory = classmethod(
                        _webapp_request_handler_factory)
                else:
                    # Compatible with webapp2.RequestHandler.
                    handler.factory = classmethod(
                        lambda cls, req, rsp: cls(req, rsp))

                factory = handler.factory
            except TypeError:
                # A "view" function.
                handler.factory = factory = handler

        return factory(request, response)

    def set_builder(self, func):
        """Sets the function called for building URIs.

        :param func:
            A function that receives ``(router, request, name, args, kwargs)``
            and returns a URI.
        """
        self.build = lambda *args, **kwargs: func(self, *args, **kwargs)

    def default_builder(self, request, name, args, kwargs):
        """Returns a URI for a named :class:`Route`.

        :param request:
            The current :class:`Request` object.
        :param name:
            The route name.
        :param args:
            Tuple of positional arguments to build the URI. All positional
            variables defined in the route must be passed and must conform
            to the format set in the route. Extra arguments are ignored.
        :param kwargs:
            Dictionary of keyword arguments to build the URI. All variables
            not set in the route default values must be passed and must
            conform to the format set in the route. Extra keywords are
            appended as a query string.

            A few keywords have special meaning:

            - **_full**: If True, builds an absolute URI.
            - **_scheme**: URI scheme, e.g., `http` or `https`. If defined,
              an absolute URI is always returned.
            - **_netloc**: Network location, e.g., `www.google.com`. If
              defined, an absolute URI is always returned.
            - **_fragment**: If set, appends a fragment (or "anchor") to the
              generated URI.
        :returns:
            An absolute or relative URI.
        """
        route = self.build_routes.get(name)
        if not route:
            raise KeyError('Route "%s" is not defined.' % name)

        return route.build(request, args, kwargs)

    def __repr__(self):
        routes = self.match_routes + [v for k, v in \
            self.build_routes.iteritems() if v not in self.match_routes]

        return '<Router(%r)>' % routes


class Config(dict):
    """A simple configuration dictionary for the :class:`WSGIApplication`."""

    #: Loaded configurations.
    loaded = None

    def __init__(self, defaults=None):
        dict.__init__(self, defaults or ())
        self.loaded = []

    def load_config(self, key, default_values=None, user_values=None,
                    required_keys=None):
        """Returns a configuration for a given key.

        This can be used by objects that define a default configuration. It
        will update the app configuration with the default values the first
        time it is requested, and mark the key as loaded.

        :param key:
            A configuration key.
        :param default_values:
            Default values defined by a module or class.
        :param user_values:
            User values, used when an object can be initialized with
            configuration. This overrides the app configuration.
        :param required_keys:
            Keys that can not be None.
        :raises:
            Exception, when a required key is None.
        """
        if key in self.loaded:
            return self[key]

        config = dict(default_values or ())

        if key in self:
            config.update(self[key])

        if user_values:
            config.update(user_values)

        if required_keys:
            for required_key in required_keys:
                if config.get(required_key) is None:
                    raise Exception('Config key %r for %r is required.' %
                        (required_key, key))

        self[key] = config
        self.loaded.append(key)
        return config


class RequestContext(object):
    """Context for a single request.

    The context is responsible for setting and cleaning global variables for
    a request.
    """

    #: A :class:`WSGIApplication` instance.
    app = None
    #: WSGI environment dictionary.
    environ = None

    def __init__(self, app, environ):
        """Initializes the request context.

        :param app:
            An :class:`WSGIApplication` instance.
        :param environ:
            A WSGI environment dictionary.
        """
        self.app = app
        self.environ = environ

    def __enter__(self):
        """Enters the request context.

        :returns:
            A tuple ``(request, response)``.
        """
        # Build request and response.
        request = self.app.request_class(self.environ)
        response = self.app.response_class()
        # Make active app and response available through the request object.
        request.app = self.app
        request.response = response
        # Register global variables.
        self.app.set_globals(app=self.app, request=request)
        return request, response

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the request context.

        This release the context locals except if an exception is caught
        in debug mode. In this case they are kept to be inspected.
        """
        if exc_type is None or not self.app.debug:
            # Unregister global variables.
            self.app.set_globals(app=None, request=None)


class WSGIApplication(object):
    """A WSGI-compliant application."""

    #: Allowed request methods.
    allowed_methods = frozenset(('GET', 'POST', 'HEAD', 'OPTIONS', 'PUT',
                                 'DELETE', 'TRACE'))
    #: Class used for the request object.
    request_class = Request
    #: Class used for the response object.
    response_class = Response
    #: Class used for the router object.
    router_class = Router
    #: Class used for the request context object.
    request_context_class = RequestContext
    #: Class used for the configuration object.
    config_class = Config
    #: A general purpose flag to indicate development mode: if True, uncaught
    #: exceptions are raised instead of using ``HTTPInternalServerError``.
    debug = False
    #: A :class:`Router` instance with all URIs registered for the application.
    router = None
    #: A :class:`Config` instance with the application configuration.
    config = None
    #: A dictionary to register objects used during the app lifetime.
    registry = None
    #: A dictionary mapping HTTP error codes to callables to handle those
    #: HTTP exceptions. See :meth:`handle_exception`.
    error_handlers = None
    #: Active :class:`WSGIApplication` instance. See :meth:`set_globals`.
    app = None
    #: Active :class:`Request` instance. See :meth:`set_globals`.
    request = None
    #: Same as :attr:`app`, for webapp compatibility. See :meth:`set_globals`.
    active_instance = None

    def __init__(self, routes=None, debug=False, config=None):
        """Initializes the WSGI application.

        :param routes:
            A list of :class:`Route` instances. For compatibility with webapp,
            the list items can also be a tuple ``(regex, handler_class)``.
        :param debug:
            True to enable debug mode, False otherwise.
        :param config:
            A configuration dictionary for the application.
        """
        self.debug = debug
        self.registry = {}
        self.error_handlers = {}
        self.set_globals(app=self)
        self.config = self.config_class(config)
        self.router = self.router_class(routes)

    def set_globals(self, app=None, request=None):
        """Registers the global variables for app and request.

        App Engine doesn't support threading, so we just assign them directly
        as class attributes of the :class:`WSGIApplication`.

        For threaded environments, direct assignment must be replaced by
        assigning to a proxy object that returns app and request using
        thread-local. Check :class:`webapp2_extras.local_app.WSGIApplication`
        for an example.

        :param app:
            A :class:`WSGIApplication` instance or None to remove it from
            the globals.
        :param request:
            A :class:`Request` instance or None to remove it from the globals.
        """
        WSGIApplication.app = WSGIApplication.active_instance = app
        WSGIApplication.request = request

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in.

        :param environ:
            A WSGI environment.
        :param start_response:
            A callable accepting a status code, a list of headers and an
            optional exception context to start the response.
        :returns:
            An iterable with the response to return to the client.
        """
        with self.request_context_class(self, environ) as (request, response):
            try:
                if request.method not in self.allowed_methods:
                    # 501 Not Implemented.
                    raise exc.HTTPNotImplemented()

                rv = self.router.dispatch(request, response)
                if rv is not None:
                    response = rv
            except Exception, e:
                try:
                    # Try to handle it with a custom error handler.
                    rv = self.handle_exception(request, response, e)
                    if rv is not None:
                        response = rv
                except HTTPException, e:
                    # Use the HTTP exception as response.
                    response = e
                except Exception, e:
                    # Error wasn't handled so we have nothing else to do.
                    return self._internal_error(e, environ, start_response)

            try:
                return response(environ, start_response)
            except Exception, e:
                return self._internal_error(e, environ, start_response)

    def _internal_error(self, exception, environ, start_response):
        logging.exception(exception)
        if self.debug:
            raise

        return exc.HTTPInternalServerError()(environ, start_response)

    def handle_exception(self, request, response, e):
        """Handles a uncaught exception occurred in :meth:`__call__`.

        Uncaught exceptions can be handled by error handlers registered in
        :attr:`error_handlers`. This is a dictionary that maps HTTP status
        codes to callables that will handle the corresponding error code.
        If the exception is not an ``HTTPException``, the status code 500
        is used.

        The error handlers receive (request, response, exception) and can be
        a callable or a string in dotted notation to be lazily imported.

        If no error handler is found, the exception is re-raised.

        Based on idea from `Flask`_.

        :param request:
            A :class:`Request` instance.
        :param request:
            A :class:`Response` instance.
        :param e:
            The uncaught exception.
        :returns:
            The returned value from the error handler.
        """
        if isinstance(e, HTTPException):
            code = e.code
        else:
            code = 500

        handler = self.error_handlers.get(code)
        if handler:
            if isinstance(handler, basestring):
                self.error_handlers[code] = handler = import_string(handler)

            return handler(request, response, e)
        else:
            # Re-raise it to be caught by the WSGI app.
            raise

    def run(self, bare=False):
        """Runs this WSGI-compliant application in a CGI environment.

        This uses functions provided by ``google.appengine.ext.webapp.util``:
        ``run_bare_wsgi_app`` and ``run_wsgi_app``.

        :param bare:
            If True, doesn't add registered WSGI middleware: use
            ``run_bare_wsgi_app`` instead of ``run_wsgi_app``.
        """
        if bare:
            util.run_bare_wsgi_app(self)
        else:
            util.run_wsgi_app(self)

    def get_response(self, *args, **kwargs):
        """Creates a request and returns a response for this app.

        This is a convenience for unit testing purposes. It receives
        parameters to build a request and calls the application, returning
        the resulting response::

            class HelloHandler(webapp2.RequestHandler):
                def get(self):
                    self.response.write('Hello, world!')

            app = webapp2.WSGIapplication([('/', HelloHandler)])

            # Test the app, passing parameters to build a request.
            response = app.get_response('/')
            assert response.status == '200 OK'
            assert response.body == 'Hello, world!'

        :param args:
            Positional arguments to be passed to ``Request.blank()``.
        :param kwargs:
            Keyword arguments to be passed to ``Request.blank()``.
        :returns:
            A :class:`Response` object.
        """
        return self.request_class.blank(*args, **kwargs).get_response(self)


def get_app():
    """Returns the active app instance.

    :returns:
        A :class:`WSGIApplication` instance.
    :raises:
        ``AssertionError`` if the app is not set.
    """
    app = WSGIApplication.app
    assert app is not None, 'WSGIApplication.app is not set.'
    return app


def get_request():
    """Returns the active request instance.

    :returns:
        A :class:`Request` instance.
    :raises:
        ``AssertionError`` if the request is not set.
    """
    request = WSGIApplication.request
    assert request is not None, 'WSGIApplication.request is not set.'
    return request


def uri_for(_name, *args, **kwargs):
    """A standalone uri_for version that can be passed to templates.

    .. seealso:: :meth:`Router.build`.
    """
    request = get_request()
    return request.app.router.build(request, _name, args, kwargs)


def abort(code, *args, **kwargs):
    """Raises an ``HTTPException``.

    :param code:
        An integer that represents a valid HTTP status code.
    :param args:
        Positional arguments to instantiate the exception.
    :param kwargs:
        Keyword arguments to instantiate the exception.
    """
    cls = exc.status_map.get(code)
    if not cls:
        raise KeyError('No exception is defined for code %r.' % code)

    raise cls(*args, **kwargs)


def import_string(import_name, silent=False):
    """Imports an object based on a string in dotted notation.

    Simplified version of the function with same name from `Werkzeug`_.

    :param import_name:
        The dotted name for the object to import.
    :param silent:
        If True, import or attribute errors are ignored and None is returned
        instead of raising an exception.
    :returns:
        The imported object.
    """
    import_name = _to_utf8(import_name)
    try:
        if '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
            return getattr(__import__(module, None, None, [obj]), obj)
        else:
            return __import__(import_name)
    except (ImportError, AttributeError):
        if not silent:
            raise


def urlunsplit(scheme=None, netloc=None, path=None, query=None, fragment=None):
    """Similar to ``urlparse.urlunsplit``, but will escape values and
    urlencode and sort query arguments.

    :param scheme:
        URI scheme, e.g., `http` or `https`.
    :param netloc:
        Network location, e.g., `localhost:8080` or `www.google.com`.
    :param path:
        URI path.
    :param query:
        URI query as an escaped string, or a dictionary or list of key-values
        tuples to build a query.
    :param fragment:
        Fragment identifier, also known as "anchor".
    :returns:
        An assembled absolute or relative URI.
    """
    if not scheme or not netloc:
        scheme = None
        netloc = None

    if path:
        path = urllib.quote(_to_utf8(path))

    if query and not isinstance(query, basestring):
        if isinstance(query, dict):
            query = query.iteritems()

        # Sort args: commonly needed to build signatures for services.
        query = urllib.urlencode(sorted(query))

    if fragment:
        fragment = urllib.quote(_to_utf8(fragment))

    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))


def _get_handler_methods(handler):
    """Returns a list of HTTP methods supported by a handler.

    :param handler:
        A :class:`RequestHandler` instance.
    :returns:
        A list of HTTP methods supported by the handler.
    """
    methods = []
    for method in get_app().allowed_methods:
        if getattr(handler, _normalize_handler_method(method), None):
            methods.append(method)

    return methods


def _webapp_request_handler_factory(cls, request, response):
    """A factory to dispatch a ``webapp.RequestHandler``."""
    handler = cls()
    handler.initialize(request, response)
    method = getattr(handler, _normalize_handler_method(request.method), None)
    if not method:
        abort(501)

    # The handler only receives *args if no named variables are set.
    args, kwargs = request.route_args, request.route_kwargs
    if kwargs:
        args = ()

    try:
        method(*args, **kwargs)
    except Exception, e:
        handler.handle_exception(e, request.app.debug)


def _normalize_handler_method(method):
    """Transforms an HTTP method into a valid Python identifier."""
    return method.lower().replace('-', '_')


def _to_utf8(value):
    """Encodes a unicode value to UTF-8 if not yet encoded."""
    if isinstance(value, str):
        return value

    return value.encode('utf-8')


Request.ResponseClass = Response
Response.RequestClass = Request
