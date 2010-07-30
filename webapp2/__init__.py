# -*- coding: utf-8 -*-
"""
    webapp2
    =======

    Taking Google App Engine's webapp to the next level!

    :copyright: 2010 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
import logging
import re
import sys
import urllib
import urlparse

from google.appengine.ext.webapp import Request
from google.appengine.ext.webapp.util import run_wsgi_app, run_bare_wsgi_app

from django.utils import simplejson

import webob
import webob.exc

#: Allowed request methods.
_ALLOWED_METHODS = frozenset(['get', 'post', 'head', 'options', 'put',
    'delete', 'trace'])

#: Regex for URL definitions.
_ROUTE_REGEX = re.compile(r'''
    \{            # The exact character "{"
    (\w+)         # The variable name (restricted to a-z, 0-9, _)
    (?::([^}]+))? # The optional :regex part
    \}            # The exact character "}"
    ''', re.VERBOSE)

#: Loaded lazy handlers.
_HANDLERS = {}

#: Value used for required values.
REQUIRED_VALUE = object()

#: Value used for missing default values.
DEFAULT_VALUE = object()


class Response(webob.Response):
    """Abstraction for an HTTP response.

    Implements all of ``webapp.Response`` interface, except ``wsgi_write()``
    as the response itself is returned by the WSGI application.
    """
    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args, **kwargs)

        # webapp uses self.response.out.write(...)
        self.out = self.body_file

    def set_status(self, code, message=None):
        """Sets the HTTP status code of this response.

        :param message:
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
        self.app_iter = []

    @staticmethod
    def http_status_message(code):
        """Returns the default HTTP status message for the given code.

        :param code:
            The HTTP code for which we want a message.
        """
        message = webob.statusreasons.status_reasons.get(code, None)
        if not message:
            raise Error('Invalid HTTP status code: %d' % code)

        return message


class RequestHandler(object):
    """Base HTTP request handler. Clients should subclass this class.

    Subclasses should override get(), post(), head(), options(), etc to handle
    different HTTP methods.

    Implements most of ``webapp.RequestHandler`` interface.
    """
    def __init__(self, app, request, response):
        """Initializes the handler.

        :param app:
            A :class:`WSGIApplication` instance.
        :param request:
            A ``webapp.Request`` instance.
        :param response:
            A :class:`Response` instance.
        """
        self.app = app
        self.request = request
        self.response = response

    def __call__(self, _method_name, *args, **kwargs):
        """Dispatches the requested method.

        :param _method_name:
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
        method = getattr(self, _method_name, None)
        if method is None:
            # 405 Method Not Allowed.
            # The response MUST include an Allow header containing a
            # list of valid methods for the requested resource.
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.6
            valid = ', '.join(get_valid_methods(self))
            self.abort(405, headers=[('Allow', valid)])

        # Execute the method.
        method(*args, **kwargs)

    def error(self, code):
        """Clears the response output stream and sets the given HTTP error
        code. This doesn't stop code execution; the response is still
        available to be filled.

        :param code:
            HTTP status error code (e.g., 501).
        """
        self.response.set_status(code)
        self.response.clear()

    def abort(self, code, *args, **kwargs):
        """Raises an :class:`webob.exc.HTTPException`. This stops code
        execution, leaving the HTTP exception to be handled by an exception
        handler.

        :param code:
            HTTP status error code (e.g., 404).
        :param args:
            Positional arguments to be passed to the exception class.
        :param kwargs:
            Keyword arguments to be passed to the exception class.
        """
        abort(code, *args, **kwargs)

    def redirect(self, uri, permanent=False):
        """Issues an HTTP redirect to the given relative URL.

        :param uri:
            A relative or absolute URI (e.g., '../flowers.html').
        :param permanent:
            If True, uses a 301 redirect instead of a 302 redirect.
        """
        if permanent:
            self.response.set_status(301)
        else:
            self.response.set_status(302)

        absolute_url = urlparse.urljoin(self.request.uri, uri)
        self.response.headers['Location'] = str(absolute_url)
        self.response.clear()

    def redirect_to(self, name, _secure=False, _anchor=None, _permanent=False,
        **kwargs):
        """Convenience method mixing :meth:`redirect` and :meth:`url_for`:
        Issues an HTTP redirect to a named URL build using :meth:`url_for`.

        :param name:
            The route name to redirect to.
        :param _secure:
            If True, redirects to a URL using `https` scheme.
        :param _anchor:
            An anchor to append to the end of the redirected URL.
        :param _permanent:
            If True, uses a 301 redirect instead of a 302 redirect.
        :param kwargs:
            Keyword arguments to build the URL.
        """
        uri = self.url_for(name, _full=_full, _secure=_secure, _anchor=_anchor,
            **kwargs)
        self.redirect(uri, permanent=_permanent)

    def url_for(self, name, _full=False, _secure=False, _anchor=None, **kwargs):
        """Builds and returns a URL for a named :class:`Route`.

        For example, if you have these routes registered in the application::

            app = WSGIApplication([
                ('/',     'handlers.HomeHandler', 'home/main'),
                ('/wiki', WikiHandler,            'wiki/start'),
            ])

        Here are some examples of how to generate URLs for them:

        >>> url = self.url_for('home/main')
        /
        >>> url = self.url_for('home/main', _full=True)
        http://localhost:8080/
        >>> url = self.url_for('wiki/start')
        /wiki
        >>> url = self.url_for('wiki/start', _full=True)
        http://localhost:8080/wiki
        >>> url = self.url_for('wiki/start', _full=True, _anchor='my-heading')
        http://localhost:8080/wiki#my-heading

        :param name:
            The route name.
        :param _full:
            If True, returns an absolute URL. Otherwise returns a relative one.
        :param _secure:
            If True, returns an absolute URL using `https` scheme.
        :param _anchor:
            An anchor to append to the end of the URL.
        :param kwargs:
            Keyword arguments to build the URL.
        :returns:
            An absolute or relative URL.
        """
        url = self.request.url_for(name, **kwargs)

        if _full or _secure:
            scheme = 'http'
            if _secure:
                scheme += 's'

            url = '%s://%s%s' % (scheme, self.request.host, url)

        if _anchor:
            url += '#%s' % url_escape(_anchor)

        return url

    def get_config(self, module, key=None, default=DEFAULT_VALUE):
        """Returns a configuration value for a module.

        See :meth:`WSGIApplication.get_config`.
        """
        return self.app.get_config(module, key=key, default=default)

    def handle_exception(self, exception, debug_mode):
        """Called if this handler throws an exception during execution.

        The default behavior is to raise the exception to be handled by
        :meth:`WSGIApplication.handle_exception`.

        :param exception:
            The exception that was thrown.
        :debug_mode:
            True if the web application is running in debug mode.
        """
        if sys.exc_info()[0]:
            raise


class RedirectHandler(RequestHandler):
    """Redirects to the given URL for all GET requests. This is meant to be
    used when defining URL routes. You must provide the keyword argument
    *url* in the route. Example::

        app = WSGIApplication([
            ('/old-url', RedirectHandler, 'legacy-url', {'url': '/new-url'}),
        ])

    Based on idea from `Tornado`_.
    """
    def get(self, **kwargs):
        url = kwargs.get('url', '/')

        if callable(url):
            url = url(self, **kwargs)

        self.redirect(url, permanent=kwargs.get('permanent', True))


class WSGIApplication(object):
    """Wraps a set of webapp RequestHandlers in a WSGI-compatible application.

    To use this class, pass a list of (URI regular expression, RequestHandler)
    pairs to the constructor, and pass the class instance to a WSGI handler.
    See the example in the module comments for details.

    The URL mapping is first-match based on the list ordering.
    """
    #: Default class used for the request object.
    request_class = Request
    #: Default class used for the response object.
    response_class = Response
    #: A dictionary mapping HTTP error codes to :class:`RequestHandler`
    #: classes used to handle them. The handler set for status 500 is used
    #: as default if others are not set.
    error_handlers = {}

    def __init__(self, url_map, debug=False, config=None):
        """Initializes the WSGI application.

        :param url_map:
            A list of URL route definitions.
        :param debug:
            True if this is debug mode, False otherwise.
        :param config:
            A configuration dictionary for the application.
        """
        self.set_router(url_map)
        self.debug = debug
        self.config = Config(config)

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in. Calls :meth:`wsgi_app`."""
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        """This is the actual WSGI application.  This is not implemented in
        :meth:`__call__` so that middlewares can be applied without losing a
        reference to the class. So instead of doing this::

            app = MyMiddleware(app)

        It's a better idea to do this instead::

            app.wsgi_app = MyMiddleware(app.wsgi_app)

        Then you still have the original application object around and
        can continue to call methods on it.

        This idea comes from `Flask <http://flask.pocoo.org/>`_.

        :param environ:
            A WSGI environment.
        :param start_response:
            A callable accepting a status code, a list of headers and an
            optional exception context to start the response.
        """
        request = self.request_class(environ)
        response = self.response_class()
        method = environ['REQUEST_METHOD'].lower()

        try:
            if method not in _ALLOWED_METHODS:
                # 501 Not Implemented.
                abort(501)

            handler_class, args, kwargs = self.match_route(request)

            if handler_class:
                handler = handler_class(self, request, response)
                try:
                    handler(method, *args, **kwargs)
                except Exception, e:
                    # If the handler implements exception handling,
                    # let it handle it.
                    handler.handle_exception(e, self.debug)
            else:
                # 404 Not Found.
                abort(404)
        except Exception, e:
            try:
                self.handle_exception(request, response, e)
            except webob.exc.WSGIHTTPException, e:
                # Use the exception as response.
                response = e
            except Exception, e:
                # Our last chance to handle the error.
                if self.debug:
                    raise

                # 500 Internal Server Error: nothing else to do.
                response = webob.exc.HTTPInternalServerError()

        return response(environ, start_response)

    def handle_exception(self, request, response, e):
        """Handles an exception. Searches :attr:`error_handlers` for a handler
        with the eerror code, if it is a :class:`webob.exc.HTTPException`,
        or the 500 status code as fall back. Dispatches the handler if found,
        otherwise simply sets the error code in the response.

        :param request:
            A ``webapp.Request`` instance.
        :param response:
            A :class:`Response` instance.
        :param e:
            The raised exception.
        """
        logging.exception(e)
        if self.debug:
            raise

        if isinstance(e, webob.exc.HTTPException):
            code = e.code
        else:
            code = 500

        handler = self.error_handlers.get(code, self.error_handlers.get(500))
        if handler:
            # Handle the exception using a custom handler.
            handler(self, request, response)('get', exception=e)
        else:
            # No exception handler. Catch it in the WSGI app.
            raise

    def set_router(self, url_map):
        """Sets a :class:`Router` instance for the given url_map.

        :param url_map:
            A list of URL route definitions.
        """
        self.router = Router()
        for spec in url_map:
            if len(spec) == 2:
                # (path, handler)
                self.router.add(*spec)
            elif len(spec) == 3:
                if not isinstance(spec[2], dict):
                    # (path, handler, name)
                    self.router.add(*spec)
                else:
                    # (path, handler, defaults)
                    self.router.add(*spec[:2], **spec[2])
            elif len(spec) == 4:
                # (path, handler, name, defaults)
                self.router.add(*spec[:3], **spec[3])

    def match_route(self, request):
        """Matches a route against the current request.

        :param request:
            A ``webapp.Request`` instance.
        :returns:
            A tuple (handler_class, args, kwargs) for the matched route.
        """
        match = self.router.match(request)
        request.url_route = match
        request.url_for = self.router.build
        if not match:
            return (None, None, None)

        route, kwargs = match
        handler_class = route.handler

        if isinstance(handler_class, basestring):
            # Lazy handler, set as a string. Import and store the class.
            if handler_class not in _HANDLERS:
                _HANDLERS[handler_class] = import_string(handler_class)

            handler_class = _HANDLERS[handler_class]

        return handler_class, (), kwargs

    def get_config(self, module, key=None, default=DEFAULT_VALUE):
        """Returns a configuration value for a module. If it is not already
        set, loads a ``default_config`` variable from the given module,
        updates the app configuration with those default values and returns
        the value for the given key. If the key is still not available,
        returns the provided default value or raises an exception if no
        default was provided.

        Every Webapp module that allows some kind of configuration sets a
        ``default_config`` global variable that is loaded by this function,
        cached and used in case the requested configuration was not defined
        by the user.

        :param module:
            The configured module.
        :param key:
            The config key.
        :returns:
            A configuration value.
        """
        config = self.config
        if module not in config.loaded:
            # Load default configuration and update app config.
            values = import_string(module + '.default_config', silent=True)
            if values:
                config.setdefault(module, values)

            config.loaded.append(module)

        value = config.get(module, key, default)
        if value not in (DEFAULT_VALUE, REQUIRED_VALUE):
            return value

        if key is None:
            raise KeyError('Module %s is not configured.' % module)
        else:
            raise KeyError('Module %s requires the config key "%s" to be '
                'set.' % (module, key))


class Route(object):
    """A URL route definition."""
    def __init__(self, path, handler, **defaults):
        """Initializes a URL route.

        :param path:
            A path to be matched. Paths can contain variables enclosed in
            curly braces and an optional regular expression to be evaluated.
            Some examples::

                route = Route('/blog', BlogHandler)
                route = Route('/blog/archive/{year:\d\d\d\d}', BlogArchiveHandler)
                route = Route('/blog/archive/{year:\d\d\d\d}/{slug}', BlogItemHandler)

        :param handler:
            A :class:`RequestHandler` class to be executed when this route
            matches.
        :param defaults:
            Default or extra keywords to be returned by this route. Default
            values present in the route variables are used to build the URL
            if the value is not passed.
        """
        # The path to be matched.
        self.path = path
        # The handler that is executed when this route matches.
        self.handler = handler
        # Default values to build the rule and extra values to be returned.
        self.defaults = defaults
        # All variables in the rule mapping to the regex to validate them.
        self.variables = {}

        last = 0
        regex = ''
        template = ''
        for match in _ROUTE_REGEX.finditer(path):
            part = path[last:match.start()]
            name = match.group(1)
            expr = match.group(2) or '[^/]+'
            last = match.end()

            regex += '%s(?P<%s>%s)' % (re.escape(part), name, expr)
            template += '%s%%(%s)s' % (part, name)
            self.variables[name] = re.compile('^%s$' % expr)

        # The regex used to match URLs.
        self.regex = re.compile('^%s%s$' % (regex, re.escape(path[last:])))
        # The template used to build URLs.
        self.template = template + path[last:]

    def match(self, request):
        """Matches a route against the current request.

        :param request:
            A ``webapp.Request`` instance.
        :returns:
            A tuple (route, route_values), including the default values if any.
        """
        match = self.regex.match(request.path)
        if match:
            values = self.defaults.copy()
            values.update(match.groupdict())
            return (self, values)

    def build(self, **kwargs):
        """Builds a URL for this route. Examples:

        >>> route = Route('/blog', BlogHandler)
        >>> route.build()
        /blog
        >>> Route('/blog/archive/{year:\d\d\d\d}', BlogArchiveHandler)
        >>> route.build(year=2010)
        /blog/2010
        >>> Route('/blog/archive/{year:\d\d\d\d}/{month:\d\d}/{slug}', BlogItemHandler)
        >>> route.build(year='2010', month='07', slug='my-blog-post')
        /blog/2010/07/my-blog-post

        :param kwargs:
            Keyword arguments to build the URL. All route variables that are
            not set as defaults must be passed, and they must conform to the
            format set in the route. Extra keywords are appended as URL
            arguments.
        :returns:
            A formatted URL.
        """
        required = self.variables.keys()
        values = {}
        for name in required:
            value = kwargs.pop(name, self.defaults.get(name))
            if not value:
                raise ValueError('Missing keyword "%s" to build URL.' % name)

            if not isinstance(value, basestring):
                value = str(value)

            value = url_escape(value)
            match = self.variables[name].match(value)
            if not match:
                raise ValueError('URL buiding error: Value "%s" is not '
                    'supported for keyword "%s".' % (value, name))

            values[name] = value

        url = self.template % values

        # Cleanup and encode extra kwargs.
        kwargs = [(to_utf8(k), to_utf8(v)) for k, v in kwargs.iteritems() \
            if isinstance(v, basestring)]

        if kwargs:
            # Append extra keywords as URL arguments.
            url += '?%s' % urllib.urlencode(kwargs)

        return url


class Router(object):
    """A simple URL router. This is used to match the current URL and build
    URLs for other resources.

    This router doesn't intend to do fancy things such as automatic URL
    redirect or subdomain matching. It should stay as simple as possible.

    Based on `Another Do-It-Yourself Framework`_ by Ian Bicking. We added
    URL building and separate :class:`Route` objects.
    """
    def __init__(self):
        self.routes = []
        self.route_names = {}

    def add(self, path, handler, _name=None, **kwargs):
        """Adds a route to this router.

        :param path:
            The route path. See :meth:`Route.__init__`.
        :param handler:
            A :class:`RequestHandler` class to be executed when this route
            matches.
        :param _name:
            The route name.
        """
        route = Route(path, handler, **kwargs)
        self.routes.append(route)
        if _name:
            self.route_names[_name] = route

    def match(self, request):
        """Matches all routes against the current request. The first one that
        matches is returned.

        :param request:
            A ``webapp.Request`` instance.
        :returns:
            A tuple (route, route_values), including the default values.
        """
        for route in self.routes:
            match = route.match(request)
            if match:
                return match

    def build(self, name, **kwargs):
        """Builds a URL for a named :class:`Route`.

        :param name:
            The route name, as registered in :meth:`add`.
        :param kwargs:
            Keyword arguments to build the URL. All route variables that are
            not set as defaults must be passed, and they must conform to the
            format set in the route. Extra keywords are appended as URL
            arguments.
        :returns:
            A formatted URL.
        """
        route = self.route_names.get(name, None)
        if not route:
            raise KeyError('Route "%s" is not defined.' % name)

        return route.build(**kwargs)


class LazyObject(object):
    """An object that is only imported when called. Example::

        handler_class = LazyObject('my.module.MyHandler')
        handler = handler_class(app, request, response)
    """
    def __init__(self, import_name):
        """Initializes a lazy object.

        :param import_name:
            The dotted name for the object to import, e.g.,
            ``my.module.MyClass``.
        """
        self.import_name = import_name
        self.obj = None

    def __call__(self, *args, **kwargs):
        if self.obj is None:
            self.obj = import_string(self.import_name)

        return self.obj(*args, **kwargs)


class Config(dict):
    """A simple configuration dictionary keyed by module name. This is a
    dictionary of dictionaries. It requires all values to be dictionaries
    and applies updates and default values to the inner dictionaries instead
    of the first level one.
    """
    #: Loaded module configurations.
    loaded = None

    def __init__(self, value=None, default=None, loaded=None):
        """Initializes the configuration object.

        :param value:
            A dictionary of configuration dictionaries for modules.
        :param default:
            A dictionary of configuration dictionaries for default values.
        :param loaded:
            A list of modules to be marked as loaded.
        """
        self.loaded = loaded or []
        if value is not None:
            assert isinstance(value, dict)
            for module in value.keys():
                self.update(module, value[module])

        if default is not None:
            assert isinstance(default, dict)
            for module in default.keys():
                self.setdefault(module, default[module])

    def __setitem__(self, module, value):
        """Sets a configuration for a module, requiring it to be a dictionary.

        :param module:
            A module name for the configuration, e.g.: 'webapp2.plugins.i18n'.
        :param value:
            A dictionary of configurations for the module.
        """
        assert isinstance(value, dict)
        super(Config, self).__setitem__(module, value)

    def update(self, module, value):
        """Updates the configuration dictionary for a module.

        >>> cfg = Config({'webapp2.plugins.i18n': {'locale': 'pt_BR'})
        >>> cfg.get('webapp2.plugins.i18n', 'locale')
        pt_BR
        >>> cfg.get('webapp2.plugins.i18n', 'foo')
        None
        >>> cfg.update('webapp2.plugins.i18n', {'locale': 'en_US', 'foo': 'bar'})
        >>> cfg.get('webapp2.plugins.i18n', 'locale')
        en_US
        >>> cfg.get('webapp2.plugins.i18n', 'foo')
        bar

        :param module:
            The module to update the configuration, e.g.:
            'webapp2.plugins.i18n'.
        :param value:
            A dictionary of configurations for the module.
        :returns:
            None.
        """
        assert isinstance(value, dict)
        if module not in self:
            self[module] = {}

        self[module].update(value)

    def setdefault(self, module, value):
        """Sets a default configuration dictionary for a module.

        >>> cfg = Config({'webapp2.plugins.i18n': {'locale': 'pt_BR'})
        >>> cfg.get('webapp2.plugins.i18n', 'locale')
        pt_BR
        >>> cfg.get('webapp2.plugins.i18n', 'foo')
        None
        >>> cfg.setdefault('webapp2.plugins.i18n', {'locale': 'en_US', 'foo': 'bar'})
        >>> cfg.get('webapp2.plugins.i18n', 'locale')
        pt_BR
        >>> cfg.get('webapp2.plugins.i18n', 'foo')
        bar

        :param module:
            The module to set default configuration, e.g.:
            'webapp2.plugins.i18n'.
        :param value:
            A dictionary of configurations for the module.
        :returns:
            None.
        """
        assert isinstance(value, dict)
        if module not in self:
            self[module] = {}

        for key in value.keys():
            self[module].setdefault(key, value[key])

    def get(self, module, key=None, default=None):
        """Returns a configuration value for given key in a given module.

        >>> cfg = Config({'webapp2.plugins.i18n': {'locale': 'pt_BR'})
        >>> cfg.get('webapp2.plugins.i18n')
        {'locale': 'pt_BR'}
        >>> cfg.get('webapp2.plugins.i18n', 'locale')
        pt_BR
        >>> cfg.get('webapp2.plugins.i18n', 'invalid-key')
        None
        >>> cfg.get('webapp2.plugins.i18n', 'invalid-key', 'default-value')
        default-value

        :param module:
            The module to get a configuration from, e.g.:
            'webapp2.plugins.i18n'.
        :param key:
            The key from the module configuration.
        :param default:
            A default value to return in case the configuration for
            the module/key is not set.
        :returns:
            The configuration value.
        """
        if module not in self:
            return default

        if key is None:
            return self[module]
        elif key not in self[module]:
            return default

        return self[module][key]


def abort(code, *args, **kwargs):
    """Raises a ``webob.exc.HTTPException``. The exception is instantiated
    passing *args* and *kwargs*.

    :param code:
        A valid HTTP error code.
    :param args:
        Arguments to be used to instantiate the exception.
    :param kwargs:
        Keyword arguments to be used to instantiate the exception.
    """
    cls = get_exception_class(code) or get_exception_class(500)
    raise cls(*args, **kwargs)


def get_valid_methods(handler):
    """Returns a list of HTTP methods supported by a handler.

    :param handler:
        A :class:`RequestHandler` class or instance.
    :returns:
        A list of HTTP methods supported by the handler.
    """
    return [m.upper() for m in _ALLOWED_METHODS if getattr(handler, m, None)]


def get_exception_class(code):
    """Returns an exception class from ``webob.exc.status_map``, a dictionary
    mapping status codes to subclasses of ``webob.exc.HTTPException``.

    :param code:
        A valid HTTP error code.
    :returns:
        A ``webob.exc.HTTPException`` class.
    """
    return webob.exc.status_map.get(code)


def import_string(import_name, silent=False):
    """Imports an object based on a string. If `silent` is True the return
    value will be `None` if the import fails.

    Simplified version of the function with same name from
    `Werkzeug <http://werkzeug.pocoo.org/>`.

    :param import_name:
        The dotted name for the object to import.
    :param silent:
        If True, import errors are ignored and None is returned instead.
    :returns:
        The imported object.
    """
    import_name = to_utf8(import_name)
    try:
        if '.' in import_name:
            module, obj = import_name.rsplit('.', 1)
        else:
            return __import__(import_name)

        return getattr(__import__(module, None, None, [obj]), obj)
    except (ImportError, AttributeError):
        if not silent:
            raise


def json_encode(value):
    """JSON-encodes the given Python object.

    This function comes from `Tornado`_.

    :param value:
        Value to be JSON-encoded.
    :returns:
        A JSON string.
    """
    # JSON permits but does not require forward slashes to be escaped.
    # This is useful when json data is emitted in a <script> tag
    # in HTML, as it prevents </script> tags from prematurely terminating
    # the javscript.  Some json libraries do this escaping by default,
    # although python's standard library does not, so we do it here.
    # http://stackoverflow.com/questions/1580647/json-why-are-forward-slashes-escaped
    return simplejson.dumps(value).replace("</", "<\\/")


def json_decode(value):
    """Returns Python objects for the given JSON string.

    This function comes from `Tornado`_.

    :param value:
        Value to be JSON-decoded.
    :returns:
        A decoded object.
    """
    return simplejson.loads(to_unicode(value))


def url_escape(value):
    """Returns a valid URL-encoded version of the given value.

    This function comes from `Tornado`_.

    :param value:
        A URL to be encoded.
    :returns:
        The encoded URL.
    """
    return urllib.quote_plus(to_utf8(value))


def url_unescape(value):
    """Decodes the given value from a URL.

    This function comes from `Tornado`_.

    :param value:
        A URL to be decoded.
    :returns:
        The decoded URL.
    """
    return to_unicode(urllib.unquote_plus(value))


def to_utf8(value):
    """Returns a string encoded using UTF-8.

    This function comes from `Tornado`_.

    :param value:
        A unicode or string to be encoded.
    :returns:
        The encoded string.
    """
    if isinstance(value, unicode):
        return value.encode('utf-8')

    assert isinstance(value, str)
    return value


def to_unicode(value):
    """Returns a unicode string from a string, using UTF-8 to decode if needed.

    This function comes from `Tornado`_.

    :param value:
        A unicode or string to be decoded.
    :returns:
        The decoded string.
    """
    if isinstance(value, str):
        return value.decode('utf-8')

    assert isinstance(value, unicode)
    return value
