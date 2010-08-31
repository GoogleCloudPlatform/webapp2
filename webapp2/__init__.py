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
import urllib
import urlparse

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_bare_wsgi_app, run_wsgi_app

import webob
import webob.exc

#: Base HTTP exception, set here as public interface.
HTTPException = webob.exc.HTTPException

#: Allowed request methods.
ALLOWED_METHODS = frozenset(['GET', 'POST', 'HEAD', 'OPTIONS', 'PUT',
    'DELETE', 'TRACE'])

#: Value used for required arguments.
REQUIRED_VALUE = object()

#: Regex for URL definitions.
_ROUTE_REGEX = re.compile(r'''
    \<            # The exact character "<"
    (\w*)         # The optional variable name (restricted to a-z, 0-9, _)
    (?::([^>]*))? # The optional :regex part
    \>            # The exact character ">"
    ''', re.VERBOSE)


class Request(webapp.Request):
    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        # A registry for objects used during the request lifetime.
        self.registry = {}
        # A dictionary for variables used in rendering.
        self.context = {}


class Response(webob.Response):
    """Abstraction for an HTTP response.

    Implements all of ``webapp.Response`` interface, except ``wsgi_write()``
    as the response itself is returned by the WSGI application.
    """
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
    """Base HTTP request handler. Clients should subclass this class.

    Subclasses should override get(), post(), head(), options(), etc to handle
    different HTTP methods.

    Implements most of ``webapp.RequestHandler`` interface.
    """
    def __init__(self, app=None, request=None, response=None):
        """Initializes this request handler with the given WSGI application,
        Request and Response.

        .. note::
           Parameters are optional only to support webapp's constructor which
           doesn't take any arguments. Consider them as required.

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

    def initialize(self, request, response):
        """Initializes this request handler with the given WSGI application,
        Request and Response.

        .. warning::
           This is deprecated. It is here for compatibility with webapp only.
           Use __init__() instead.

        :param request:
            A ``webapp.Request`` instance.
        :param response:
            A :class:`Response` instance.
        """
        logging.warning('RequestHandler.initialize() is deprecated. '
            'Use __init__() instead.')

        self.app = WSGIApplication.active_instance
        self.request = request
        self.response = response

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
        """Raises an :class:`HTTPException`. This stops code execution,
        leaving the HTTP exception to be handled by an exception handler.

        :param code:
            HTTP status error code (e.g., 404).
        :param args:
            Positional arguments to be passed to the exception class.
        :param kwargs:
            Keyword arguments to be passed to the exception class.
        """
        abort(code, *args, **kwargs)

    def redirect(self, uri, permanent=False, abort=False):
        """Issues an HTTP redirect to the given relative URL. This won't stop
        code execution unless **abort** is True. A common practice is to
        return when calling the function::

            return self.redirect('/some-path')

        :param uri:
            A relative or absolute URI (e.g., '../flowers.html').
        :param permanent:
            If True, uses a 301 redirect instead of a 302 redirect.
        :param abort:
            If True, raises an exception to perform the redirect.

        .. seealso:: :meth:`redirect_to`.
        """
        absolute_url = str(urlparse.urljoin(self.request.uri, uri))
        if permanent:
            code = 301
        else:
            code = 302

        if abort:
            self.abort(code, headers=[('Location', absolute_url)])

        self.response.headers['Location'] = absolute_url
        self.response.set_status(code)
        self.response.clear()

    def redirect_to(self, _name, _permanent=False, _abort=False, *args,
        **kwargs):
        """Convenience method mixing :meth:`redirect` and :meth:`url_for`:
        Issues an HTTP redirect to a named URL built using :meth:`url_for`.

        :param _name:
            The route name to redirect to.
        :param _permanent:
            If True, uses a 301 redirect instead of a 302 redirect.
        :param _abort:
            If True, raises an exception to perform the redirect.
        :param args:
            Positional arguments to build the URL.
        :param kwargs:
            Keyword arguments to build the URL.

        .. seealso:: :meth:`redirect` and :meth:`url_for`.
        """
        url = self.url_for(_name, *args, **kwargs)
        self.redirect(url, permanent=_permanent, abort=_abort)

    def url_for(self, _name, *args, **kwargs):
        """Builds and returns a URL for a named :class:`Route`.

        For example, if you have these routes defined for the application::

            app = WSGIApplication([
                Route(r'/', 'handlers.HomeHandler', 'home'),
                Route(r'/wiki', WikiHandler, 'wiki'),
                Route(r'/wiki/<page>', WikiHandler, 'wiki-page'),
            ])

        Here are some examples of how to generate URLs inside a handler::

            # /
            url = self.url_for('home')
            # http://localhost:8080/
            url = self.url_for('home', _full=True)
            # /wiki
            url = self.url_for('wiki')
            # http://localhost:8080/wiki
            url = self.url_for('wiki', _full=True)
            # http://localhost:8080/wiki#my-heading
            url = self.url_for('wiki', _full=True, _anchor='my-heading')
            # /wiki/my-first-page
            url = self.url_for('wiki-page', page='my-first-page')
            # /wiki/my-first-page?format=atom
            url = self.url_for('wiki-page', page='my-first-page', format='atom')

        :param _name:
            The route name.
        :param args:
            Positional arguments to build the URL. All positional variables
            defined in the route must be passed and must conform to the
            format set in the route. Extra arguments are ignored.
        :param kwargs:
            Keyword arguments to build the URL. All variables not set in the
            route default values must be passed and must conform to the format
            set in the route. Extra keywords are appended as URL arguments.

            A few keywords have special meaning:

            - **_full**: If True, builds an absolute URL.
            - **_scheme**: URL scheme, e.g., `http` or `https`. If defined,
              an absolute URL is always returned.
            - **_netloc**: Network location, e.g., `www.google.com`. If
              defined, an absolute URL is always returned.
            - **_anchor**: If set, appends an anchor to generated URL.
        :returns:
            An absolute or relative URL.

        .. note::
           This method, like :meth:`WSGIApplication.url_for`, needs the request
           attribute to be set to build absolute URLs. This is because some
           routes may need to retrieve information from the request to set the
           URL host. We pass the request object explicitly instead of relying
           on ``os.environ`` mainly for better testability, but it also helps
           middleware.

        .. seealso:: :meth:`Router.build`.
        """
        return self.app.router.build(_name, self.request, args, kwargs)

    def get_config(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module.

        .. seealso:: :meth:`Config.get_or_load`.
        """
        return self.app.config.get_or_load(module, key=key, default=default)

    def handle_exception(self, exception, debug_mode):
        """Called if this handler throws an exception during execution.

        The default behavior is to re-raise the exception to be handled by
        :meth:`WSGIApplication.handle_exception`.

        :param exception:
            The exception that was thrown.
        :param debug_mode:
            True if the web application is running in debug mode.
        """
        raise


class RedirectHandler(RequestHandler):
    """Redirects to the given URL for all GET requests. This is meant to be
    used when defining URL routes. You must provide at least the keyword
    argument *url* in the route default values. Example::

        def get_redirect_url(handler, *args, **kwargs):
            return handler.url_for('new-route-name')

        app = WSGIApplication([
            Route(r'/old-url', RedirectHandler, defaults={'url': '/new-url'}),
            Route(r'/other-old-url', RedirectHandler, defaults={'url': get_redirect_url}),
        ])

    Based on idea from `Tornado`_.
    """
    def get(self, *args, **kwargs):
        """Performs the redirect. Two keyword arguments can be passed through
        the URL route:

        - **url**: A URL string or a callable that returns a URL. The callable
          is called passing ``(handler, *args, **kwargs)`` as arguments.
        - **permanent**: If False, uses a 301 redirect instead of a 302
          redirect Default is True.
        """
        url = kwargs.pop('url', '/')
        permanent = kwargs.pop('permanent', True)

        if callable(url):
            url = url(self, *args, **kwargs)

        self.redirect(url, permanent=permanent)


class Config(dict):
    """A simple configuration dictionary keyed by module name. This is a
    dictionary of dictionaries. It requires all values to be dictionaries
    and applies updates and default values to the inner dictionaries instead
    of the first level one.

    The configuration object is available as a ``config`` attribute of the
    :class:`WSGIApplication`. If is instantiated and populated when the app is
    built::

        config = {}

        config['my.module'] = {
            'foo': 'bar',
        }

        app = WSGIApplication([('/', MyHandler)], config=config)

    Then to read configuration values, use :meth:`RequestHandler.get_config`::

        class MyHandler(RequestHandler):
            def get(self):
                foo = self.get_config('my.module', 'foo')

                # ...
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
            A default value to return when the configuration for the given
            key is not set. It is only returned if **key** is defined.
        :returns:
            The configuration value.
        """
        if module not in self:
            if key is None:
                return None

            return default

        if key is None:
            return self[module]

        if key not in self[module]:
            return default

        return self[module][key]

    def get_or_load(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module. If it is not already
        set, loads a ``default_config`` variable from the given module,
        updates the app configuration with those default values and returns
        the value for the given key. If the key is still not available,
        returns the provided default value or raises an exception if no
        default was provided.

        Every module that allows some kind of configuration sets a
        ``default_config`` global variable that is loaded by this function,
        cached and used in case the requested configuration was not defined
        by the user.

        :param module:
            The configured module.
        :param key:
            The config key.
        :param default:
            A default value to return in case the configuration for
            the module/key is not set.
        :returns:
            A configuration value.
        """
        if module not in self.loaded:
            # Load default configuration and update config.
            values = import_string(module + '.default_config', silent=True)
            if values:
                self.setdefault(module, values)

            self.loaded.append(module)

        value = self.get(module, key, default)

        if value is not REQUIRED_VALUE and not (key is None and value is None):
            return value

        if key is None and value is None:
            raise KeyError('Module %s is not configured.' % module)

        raise KeyError('Module %s requires the config key "%s" to be '
                'set.' % (module, key))


class BaseRoute(object):
    """Interface for URL routes. Custom routes must implement some or all
    methods and attributes from this class.
    """
    #: Route name, used to build URLs.
    name = None
    #: True if this route is only used for URL generation and never matches.
    build_only = False

    def match(self, request):
        """Matches this route against the current request.

        :param request:
            A ``webapp.Request`` instance.
        :returns:
            A tuple ``(handler, args, kwargs)`` if the route matches, or None.
        """
        raise NotImplementedError()

    def build(self, request, args, kwargs):
        """Builds and returns a URL for this route.

        :param request:
            The current ``Request`` object.
        :param args:
            Tuple of positional arguments to build the URL.
        :param kwargs:
            Dictionary of keyword arguments to build the URL.
        :returns:
            An absolute or relative URL.
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
            raise ValueError("Route %r is build_only but doesn't have a "
                "name" % self)

    def get_build_routes(self):
        """Generator to get all routes that can be built from a route.

        :yields:
            This route or all nested routes that can be built.
        """
        if self.name is not None:
            yield self


class SimpleRoute(BaseRoute):
    """A route that is compatible with webapp's routing. URL building is not
    implemented as webapp has rudimentar support for it, and this is the most
    unknown webapp feature anyway.
    """
    def __init__(self, template, handler):
        """Initializes a URL route.

        :param template:
            A regex to be matched.
        :param handler:
            A :class:`RequestHandler` class or dotted name for a class to be
            lazily imported, e.g., ``my.module.MyHandler``.
        """
        self.template = template
        self.handler = handler
        # Lazy property.
        self.regex = None

    def _regex(self):
        if not self.template.startswith('^'):
            self.template = '^' + self.template

        if not self.template.endswith('$'):
            self.template += '$'

        self.regex = re.compile(self.template)
        return self.regex

    def match(self, request):
        """Matches this route against the current request.

        .. seealso:: :meth:`BaseRoute.match`.
        """
        regex = self.regex or self._regex()
        match = regex.match(request.path)
        if match:
            return self.handler, match.groups(), {}

    def __repr__(self):
        return '<SimpleRoute(%r, %r)>' % (self.template, self.handler)

    __str__ = __repr__


class Route(BaseRoute):
    """A URL route definition. A route template contains parts enclosed by
    ``<>`` and is used to match requested URLs. Here are some examples::

        route = Route(r'/article/<id:[\d]+>', ArticleHandler)
        route = Route(r'/wiki/<page_name:\w+>', WikiPageHandler)
        route = Route(r'/blog/<year:\d{4}>/<month:\d{2}>/<day:\d{2}>/<slug:\w+>', BlogItemHandler)

    Based on `Another Do-It-Yourself Framework`_, by Ian Bicking. We added
    URL building, non-keyword variables and other improvements.
    """
    def __init__(self, template, handler=None, name=None, defaults=None,
        build_only=False):
        """Initializes a URL route.

        :param template:
            A route template to be matched, containing parts enclosed by ``<>``
            that can have only a name, only a regular expression or both:

              =============================  ==================================
              Format                         Example
              =============================  ==================================
              ``<name>``                     ``r'/<year>/<month>'``
              ``<:regular expression>``      ``r'/<:\d{4}>/<:\d{2}>'``
              ``<name:regular expression>``  ``r'/<year:\d{4}>/<month:\d{2}>'``
              =============================  ==================================

            If the name is set, the value of the matched regular expression
            is passed as keyword argument to the :class:`RequestHandler`.
            Otherwise it is passed as positional argument.

            The same template can mix parts with name, regular expression or
            both.
        :param handler:
            A :class:`RequestHandler` class or dotted name for a class to be
            lazily imported, e.g., ``my.module.MyHandler``.
        :param name:
            The name of this route, used to build URLs based on it.
        :param defaults:
            Default or extra keywords to be returned by this route. Values
            also present in the route variables are used to build the URL
            when they are missing.
        :param build_only:
            If True, this route never matches and is used only to build URLs.
        """
        self.template = template
        self.handler = handler
        self.name = name
        self.defaults = defaults or {}
        self.build_only = build_only
        # Lazy properties.
        self.regex = None
        self.variables = None
        self.reverse_template = None

    def _parse_template(self):
        self.variables = {}
        last = count = 0
        regex = reverse_template = ''
        for match in _ROUTE_REGEX.finditer(self.template):
            part = self.template[last:match.start()]
            name = match.group(1)
            expr = match.group(2) or '[^/]+'
            last = match.end()

            if not name:
                name = '__%d__' % count
                count += 1

            reverse_template += '%s%%(%s)s' % (part, name)
            regex += '%s(?P<%s>%s)' % (re.escape(part), name, expr)
            self.variables[name] = re.compile('^%s$' % expr)

        regex = '^%s%s$' % (regex, re.escape(self.template[last:]))
        self.regex = re.compile(regex)
        self.reverse_template = reverse_template + self.template[last:]
        self.has_positional_variables = count > 0

    def _regex(self):
        self._parse_template()
        return self.regex

    def _variables(self):
        self._parse_template()
        return self.variables

    def _reverse_template(self):
        self._parse_template()
        return self.reverse_template

    def match(self, request):
        """Matches this route against the current request.

        .. seealso:: :meth:`BaseRoute.match`.
        """
        regex = self.regex or self._regex()
        match = regex.match(request.path)
        if match:
            kwargs = self.defaults.copy()
            kwargs.update(match.groupdict())
            if kwargs and self.has_positional_variables:
                args = tuple(value[1] for value in sorted((int(key[2:-2]), \
                    kwargs.pop(key)) for key in \
                    kwargs.keys() if key.startswith('__')))
            else:
                args = ()

            return self.handler, args, kwargs

    def build(self, request, args, kwargs):
        """Builds a URL for this route.

        .. seealso:: :meth:`Router.build`.
        """
        full = kwargs.pop('_full', False)
        scheme = kwargs.pop('_scheme', None)
        netloc = kwargs.pop('_netloc', None)
        anchor = kwargs.pop('_anchor', None)

        if full or scheme or netloc:
            if not netloc:
                netloc = request.host

            if not scheme:
                scheme = 'http'

        path, query = self._build(args, kwargs)
        return urlunsplit(scheme, netloc, path, query, anchor)

    def _build(self, args, kwargs):
        """Builds the path for this route.

        :returns:
            A tuple ``(path, kwargs)`` with the built URL path and extra
            keywords to be used as URL query arguments.
        """
        variables = self.variables or self._variables()
        if self.has_positional_variables:
            for index, value in enumerate(args):
                key = '__%d__' % index
                if key in variables:
                    kwargs[key] = value

        values = {}
        for name, regex in variables.iteritems():
            value = kwargs.pop(name, self.defaults.get(name))
            if not value:
                raise KeyError('Missing argument "%s" to build URL.' % \
                    name.strip('_'))

            if not isinstance(value, basestring):
                value = str(value)

            if not regex.match(value):
                raise ValueError('URL buiding error: Value "%s" is not '
                    'supported for argument "%s".' % (value, name.strip('_')))

            values[name] = value

        return (self.reverse_template % values, kwargs)

    def __repr__(self):
        return '<Route(%r, %r, name=%r, defaults=%r, build_only=%r)>' % \
            (self.template, self.handler, self.name, self.defaults,
            self.build_only)

    __str__ = __repr__


class Router(object):
    """A simple URL router used to match the current URL, dispatch the handler
    and build URLs for other resources.
    """
    #: Class used when the route is a tuple. Default is compatible with webapp.
    route_class = SimpleRoute

    def __init__(self, app, routes=None):
        """Initializes the router.

        :param app:
            The :class:`WSGIApplication` instance.
        :param routes:
            A list of :class:`Route` instances to initialize the router.
        """
        self.app = app
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
            # Simple route, compatible with webapp.
            route = self.route_class(*route)

        for r in route.get_match_routes():
            self.match_routes.append(r)

        for r in route.get_build_routes():
            self.build_routes[r.name] = r

    def match(self, request):
        """Matches all routes against the current request. The first one that
        matches is returned.

        :param request:
            A ``webapp.Request`` instance.
        :returns:
            A tuple ``(route, args, kwargs)`` if a route matched, or None.
        """
        for route in self.match_routes:
            match = route.match(request)
            if match:
                request.route = route
                request.route_args, request.route_kwargs = match[1], match[2]
                return match

    def dispatch(self, app, request, response, match, method=None):
        """Dispatches a request. This calls the :class:`RequestHandler` from
        the matched :class:`Route`.

        :param app:
            A :class:`WSGIApplication` instance.
        :param request:
            A ``webapp.Request`` instance.
        :param response:
            A :class:`Response` instance.
        :param match:
            A tuple ``(handler, args, kwargs)``, resulted from the matched
            route.
        :param method:
            Handler method to be called. In cases like exception handling, a
            method can be forced instead of using the request method.
        """
        handler_class, args, kwargs = match
        method = method or request.method.lower().replace('-', '_')

        if isinstance(handler_class, basestring):
            if handler_class not in self._handlers:
                self._handlers[handler_class] = import_string(handler_class)

            handler_class = self._handlers[handler_class]

        new_style_handler = True
        try:
            handler = handler_class(app, request, response)
        except TypeError, e:
            # Support webapp's initialize().
            new_style_handler = False
            handler = handler_class()
            handler.initialize(request, response)

        try:
            if new_style_handler:
                handler(method, *args, **kwargs)
            else:
                # Support webapp handlers which don't implement __call__().
                getattr(handler, method)(*args)
        except Exception, e:
            if method == 'handle_exception':
                # We are already handling an exception.
                raise

            # If the handler implements exception handling, let it handle it.
            handler.handle_exception(e, app.debug)

    def build(self, name, request, args, kwargs):
        """Builds and returns a URL for a named :class:`Route`.

        :param name:
            The route name.
        :param request:
            The current ``Request`` object.
        :param args:
            Tuple of positional arguments to build the URL.
        :param kwargs:
            Dictionary of keyword arguments to build the URL.
        :returns:
            An absolute or relative URL.

        .. seealso:: :meth:`RequestHandler.url_for`.
        """
        route = self.build_routes.get(name)
        if not route:
            raise KeyError('Route "%s" is not defined.' % name)

        return route.build(request, args, kwargs)

    def __repr__(self):
        routes = self.match_routes + [v for k, v in \
            self.build_routes.iteritems() if v not in self.match_routes]

        return '<Router(%r)>' % routes

    __str__ = __repr__


class WSGIApplication(object):
    """Wraps a set of webapp RequestHandlers in a WSGI-compatible application.

    To use this class, pass a list of tuples ``(regex, RequestHandler class)``
    or :class:`Route` instances to the constructor, and pass the class instance
    to a WSGI handler. Example::

        from webapp2 import RequestHandler, WSGIApplication

        class HelloWorldHandler(RequestHandler):
            def get(self):
                self.response.out.write('Hello, World!')

        app = WSGIApplication([
            (r'/', HelloWorldHandler),
        ])

        def main():
            app.run()

        if __name__ == '__main__':
            main()

    The URL mapping is first-match based on the list ordering. Items in the
    list can also be an object that implements the method ``match(request)``.
    The provided class :class:`Route` is a route implementation that allows
    reversible URLs and keyword arguments passed to the handler. Example::

        app = WSGIApplication([
            Route(r'/articles', ArticlesHandler, 'articles'),
            Route(r'/articles/<id:[\d]+>', ArticleHandler, 'article'),
        ])

    .. seealso:: :class:`Route`.
    """
    #: Default class used for the request object.
    request_class = Request
    #: Default class used for the response object.
    response_class = Response
    #: Default class used for the router object.
    router_class = Router
    #: Default class used for the config object.
    config_class = Config

    def __init__(self, routes=None, debug=False, config=None):
        """Initializes the WSGI application.

        :param routes:
            List of URL definitions as tuples ``(route, RequestHandler class)``.
        :param debug:
            True if this is debug mode, False otherwise.
        :param config:
            A configuration dictionary for the application.
        """
        self.debug = debug
        self.config = self.config_class(config)
        self.router = self.router_class(self, routes)
        # A dictionary mapping HTTP error codes to :class:`RequestHandler`
        # classes used to handle them.
        self.error_handlers = {}
        # A registry for objects used during the app lifetime.
        self.registry = {}
        # For compatibility with webapp only. Don't use it!
        WSGIApplication.active_instance = self
        # Current request did not start yet, so we set a fallback.
        self.request = None

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

        This idea comes from `Flask`_.

        :param environ:
            A WSGI environment.
        :param start_response:
            A callable accepting a status code, a list of headers and an
            optional exception context to start the response.
        """
        try:
            # For compatibility with webapp only. Don't use it!
            WSGIApplication.active_instance = self

            self.request = request = self.request_class(environ)
            response = self.response_class()

            if request.method not in ALLOWED_METHODS:
                # 501 Not Implemented.
                raise webob.exc.HTTPNotImplemented()

            # Matched values are (handler, args, kwargs).
            match = self.router.match(request)

            if match:
                self.router.dispatch(self, request, response, match)
            else:
                # 404 Not Found.
                raise webob.exc.HTTPNotFound()
        except Exception, e:
            try:
                self.handle_exception(request, response, e)
            except webob.exc.WSGIHTTPException, e:
                # Use the exception as response.
                response = e
            except Exception, e:
                # Error wasn't handled so we have nothing else to do.
                logging.exception(e)
                if self.debug:
                    raise

                # 500 Internal Server Error.
                response = webob.exc.HTTPInternalServerError()
        finally:
            self.request = None

        return response(environ, start_response)

    def handle_exception(self, request, response, e):
        """Handles an exception. To set app-wide error handlers, define them
        using the corresponent HTTP status code in the ``error_handlers``
        dictionary of :class:`WSGIApplication`. For example, to set a custom
        `Not Found` page::

            class Handle404(RequestHandler):
                def handle_exception(self, exception, debug_mode):
                    self.response.out.write('Oops! I could swear this page was here!')
                    self.response.set_status(404)

            app = WSGIApplication([
                (r'/', MyHandler),
            ])
            app.error_handlers[404] = Handle404

        When an ``HTTPException`` is raised using :func:`abort` or because the
        app could not fulfill the request, the error handler defined for the
        current HTTP status code will be called. If it is not set, the
        exception is re-raised.

        .. note::
           Although being a :class:`RequestHandler`, the error handler will
           execute the ``handle_exception`` method after instantiation, instead
           of the method corresponding to the current request.

           Also, the error handler is responsible for setting the response
           status code, as shown in the example above.

        :param request:
            A ``webapp.Request`` instance.
        :param response:
            A :class:`Response` instance.
        :param e:
            The raised exception.
        """
        if isinstance(e, HTTPException):
            code = e.code
        else:
            code = 500

        handler = self.error_handlers.get(code)
        if handler:
            # Handle the exception using a custom handler.
            match = (handler, (e, self.debug), {})
            self.router.dispatch(self, request, response, match,
                method='handle_exception')
        else:
            # No exception handler. Catch it in the WSGI app.
            raise

    def url_for(self, _name, *args, **kwargs):
        """Builds and returns a URL for a named :class:`Route`.

        .. seealso:: :meth:`RequestHandler.url_for` and :meth:`Router.build`.
        """
        return self.router.build(_name, self.request, args, kwargs)

    def get_config(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module.

        .. seealso:: :meth:`Config.get_or_load`.
        """
        return self.config.get_or_load(module, key=key, default=default)

    def run(self, bare=False):
        """Runs the app using ``google.appengine.ext.webapp.util.run_wsgi_app``.
        This is generally called inside a ``main()`` function of the file
        mapped in *app.yaml* to run the application::

            # ...

            app = WSGIApplication([
                Route(r'/', HelloWorldHandler),
            ])

            def main():
                app.run()

            if __name__ == '__main__':
                main()

        :param bare:
            If True, uses ``run_bare_wsgi_app`` instead of ``run_wsgi_app``,
            which doesn't add WSGI middleware.
        """
        # Fix issue #772.
        if self.debug:
            fix_sys_path()

        if bare:
            run_bare_wsgi_app(self)
        else:
            run_wsgi_app(self)


def abort(code, *args, **kwargs):
    """Raises an ``HTTPException``. The exception is instantiated passing
    *args* and *kwargs*.

    :param code:
        A valid HTTP error code from ``webob.exc.status_map``, a dictionary
        mapping status codes to subclasses of ``HTTPException``.
    :param args:
        Arguments to be used to instantiate the exception.
    :param kwargs:
        Keyword arguments to be used to instantiate the exception.
    """
    cls = webob.exc.status_map.get(code)
    if not cls:
        raise KeyError('No exception is defined for code %r.' % code)

    raise cls(*args, **kwargs)


def get_valid_methods(handler):
    """Returns a list of HTTP methods supported by a handler.

    :param handler:
        A :class:`RequestHandler` instance.
    :returns:
        A list of HTTP methods supported by the handler.
    """
    return [method for method in ALLOWED_METHODS if getattr(handler,
        method.lower().replace('-', '_'), None)]


def import_string(import_name, silent=False):
    """Imports an object based on a string. If *silent* is True the return
    value will be None if the import fails.

    Simplified version of the function with same name from `Werkzeug`_.

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
            return getattr(__import__(module, None, None, [obj]), obj)
        else:
            return __import__(import_name)
    except (ImportError, AttributeError):
        if not silent:
            raise


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


def urlunsplit(scheme=None, netloc=None, path=None, query=None, fragment=None):
    """Similar to ``urlparse.urlunsplit``, but will escape values and
    urlencode and sort query arguments.

    :param scheme:
        URL scheme, e.g., `http` or `https`.
    :param netloc:
        Network location, e.g., `localhost:8080` or `www.google.com`.
    :param path:
        URL path.
    :param query:
        URL query as an escaped string, or a dictionary or list of key-values
        tuples to build a query.
    :param fragment:
        Fragment identifier, also known as "anchor".
    :returns:
        An assembled absolute or relative URL.
    """
    if not scheme or not netloc:
        scheme = None
        netloc = None

    if path:
        path = urllib.quote_plus(to_utf8(path), '/')

    if query and not isinstance(query, basestring):
        if isinstance(query, dict):
            query = query.items()

        query_args = []
        for key, values in query:
            if isinstance(values, basestring):
                values = (values,)

            for value in values:
                query_args.append((to_utf8(key), to_utf8(value)))

        # Sorting should be optional? Sorted args are commonly needed to build
        # URL signatures for services.
        query_args.sort()
        query = urllib.urlencode(query_args)

    if fragment:
        fragment = urllib.quote(to_utf8(fragment))

    return urlparse.urlunsplit((scheme, netloc, path, query, fragment))


_ULTIMATE_SYS_PATH = None


def fix_sys_path():
    """A fix for issue 772. We must keep this here until it is fixed in the dev
    server. I know, I don't like it either.

    See: http://code.google.com/p/googleappengine/issues/detail?id=772
    """
    global _ULTIMATE_SYS_PATH
    import sys
    if _ULTIMATE_SYS_PATH is None:
        _ULTIMATE_SYS_PATH = list(sys.path)
    elif sys.path != _ULTIMATE_SYS_PATH:
        sys.path[:] = _ULTIMATE_SYS_PATH
