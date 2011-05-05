# -*- coding: utf-8 -*-
"""
    webapp2
    =======

    Taking Google App Engine's webapp to the next level!

    :copyright: 2010 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
from __future__ import with_statement

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

# Value used for missing default values.
DEFAULT_VALUE = object()

# Value used for required values.
REQUIRED_VALUE = object()

#: Regex for URL definitions.
_ROUTE_REGEX = re.compile(r'''
    \<            # The exact character "<"
    (\w*)         # The optional variable name (restricted to a-z, 0-9, _)
    (?::([^>]*))? # The optional :regex part
    \>            # The exact character ">"
    ''', re.VERBOSE)


class Request(webapp.Request):
    #: A reference to the :class:`WSGIApplication` instance.
    app = None
    #: A reference to the matched :class:`Route`.
    route = None
    #: The matched route positional arguments.
    route_args = None
    #: The matched route keyword arguments.
    route_kwargs = None

    def __init__(self, *args, **kwargs):
        super(Request, self).__init__(*args, **kwargs)
        # A registry for objects used during the request lifetime.
        self.registry = {}


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
    #: A :class:`Request` instance.
    request = None
    #: A :class:`Response` instance.
    response = None
    #: A :class:`WSGIApplication` instance.
    app = None

    def __init__(self, request=None, response=None):
        """Initializes this request handler with the given WSGI application,
        Request and Response.

        .. note::
           Parameters are optional only to support webapp's constructor which
           doesn't take any arguments. Consider them as required.

        :param request:
            A :class:`Request` instance.
        :param response:
            A :class:`Response` instance.
        """
        if not request or not response:
            # When dispatched by webapp.WSGIApplication, both are None.
            return

        self.request = request
        self.response = response
        self.app = request.app
        self.dispatch()

    def initialize(self, request, response):
        """Initializes this request handler with the given WSGI application,
        Request and Response.

        .. warning::
           This is deprecated. It is here for compatibility with webapp only.
           Use __init__() instead.

        :param request:
            A :class:`Request` instance.
        :param response:
            A :class:`Response` instance.
        """
        from warnings import warn
        warn(DeprecationWarning('RequestHandler.initialize() is deprecated. '
            'Use __init__() instead.'))
        self.request = request
        self.response = response
        self.app = WSGIApplication.app

    def dispatch(self):
        """Dispatches the request.

        This will first check if there's a handler_method defined in the
        matched route, and if not it'll use the method correspondent to the
        request method (get, post etc).
        """
        method_name = self.request.route.handler_method
        if not method_name:
            method_name = _normalize_method(self.request.method)

        method = getattr(self, method_name, None)
        if method is None:
            # 405 Method Not Allowed.
            # The response MUST include an Allow header containing a
            # list of valid methods for the requested resource.
            # http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html#sec10.4.6
            valid = ', '.join(self.get_valid_methods())
            self.abort(405, headers=[('Allow', valid)])

        try:
            method(*self.request.route_args, **self.request.route_kwargs)
        except Exception, e:
            self.handle_exception(e, self.app.debug)

    def get_valid_methods(self):
        """Returns a list of request methods supported by this handler.

        :returns:
            A list of HTTP methods supported by this handler.
        """
        methods = []
        for method in self.app.allowed_methods:
            if getattr(self, _normalize_method(method), None):
                methods.append(method)

        return methods

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

        .. seealso:: :meth:`Config.get_config`.
        """
        return self.app.config.get_config(module, key=key, default=default)

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

        func = getattr(url, '__call__', None)
        if func:
            url = func(self, *args, **kwargs)

        self.redirect(url, permanent=permanent)


class cached_property(object):
    """A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
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

    This class was borrowed from `Werkzeug`_.
    """
    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __get__(self, obj, type=None):
        if obj is None:
            return self

        value = obj.__dict__.get(self.__name__, DEFAULT_VALUE)
        if value is DEFAULT_VALUE:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value

        return value


class Config(dict):
    """A simple configuration dictionary keyed by module name. This is a
    dictionary of dictionaries. It requires all values to be dictionaries
    and applies updates and default values to the inner dictionaries instead
    of the first level one.

    The configuration object is available as a ``config`` attribute of
    :class:`WSGIApplication`. If is instantiated and populated when the app
    is built::

        config = {}

        config['my.module'] = {
            'foo': 'bar',
        }

        app = WSGIApplication(routes=[Rule('/', name='home', handler=MyHandler)], config=config)

    Then to read configuration values, use :meth:`RequestHandler.get_config`::

        class MyHandler(RequestHandler):
            def get(self):
                foo = self.get_config('my.module', 'foo')

                # ...
    """
    #: Loaded module configurations.
    loaded = None

    def __init__(self, values=None, defaults=None):
        """Initializes the configuration object.

        :param values:
            A dictionary of configuration dictionaries for modules.
        :param defaults:
            A dictionary of configuration dictionaries for initial default
            values. These modules are marked as loaded.
        """
        self.loaded = []
        if values is not None:
            assert isinstance(values, dict)
            for module, config in values.iteritems():
                self.update(module, config)

        if defaults is not None:
            assert isinstance(defaults, dict)
            for module, config in defaults.iteritems():
                self.setdefault(module, config)
                self.loaded.append(module)

    def __getitem__(self, module):
        """Returns the configuration for a module. If it is not already
        set, loads a ``default_config`` variable from the given module and
        updates the configuration with those default values

        Every module that allows some kind of configuration sets a
        ``default_config`` global variable that is loaded by this function,
        cached and used in case the requested configuration was not defined
        by the user.

        :param module:
            The module name.
        :returns:
            A configuration value.
        """
        if module not in self.loaded:
            # Load default configuration and update config.
            values = import_string(module + '.default_config', silent=True)
            if values:
                self.setdefault(module, values)

            self.loaded.append(module)

        try:
            return dict.__getitem__(self, module)
        except KeyError:
            raise KeyError('Module %r is not configured.' % module)

    def __setitem__(self, module, values):
        """Sets a configuration for a module, requiring it to be a dictionary.

        :param module:
            A module name for the configuration, e.g.: `webapp2.ext.i18n`.
        :param values:
            A dictionary of configurations for the module.
        """
        assert isinstance(values, dict), 'Module configuration must be a dict.'
        dict.__setitem__(self, module, SubConfig(module, values))

    def get(self, module, default=DEFAULT_VALUE):
        """Returns a configuration for a module. If default is not provided,
        returns an empty dict if the module is not configured.

        :param module:
            The module name.
        :params default:
            Default value to return if the module is not configured. If not
            set, returns an empty dict.
        :returns:
            A module configuration.
        """
        if default is DEFAULT_VALUE:
            default = {}

        return dict.get(self, module, default)

    def setdefault(self, module, values):
        """Sets a default configuration dictionary for a module.

        :param module:
            The module to set default configuration, e.g.: `webapp2.ext.i18n`.
        :param values:
            A dictionary of configurations for the module.
        :returns:
            The module configuration dictionary.
        """
        assert isinstance(values, dict), 'Module configuration must be a dict.'
        if module not in self:
            dict.__setitem__(self, module, SubConfig(module))

        module_dict = dict.__getitem__(self, module)

        for key, value in values.iteritems():
            module_dict.setdefault(key, value)

        return module_dict

    def update(self, module, values):
        """Updates the configuration dictionary for a module.

        :param module:
            The module to update the configuration, e.g.: `webapp2.ext.i18n`.
        :param values:
            A dictionary of configurations for the module.
        """
        assert isinstance(values, dict), 'Module configuration must be a dict.'
        if module not in self:
            dict.__setitem__(self, module, SubConfig(module))

        dict.__getitem__(self, module).update(values)

    def get_config(self, module, key=None, default=REQUIRED_VALUE):
        """Returns a configuration value for a module and optionally a key.
        Will raise a KeyError if they the module is not configured or the key
        doesn't exist and a default is not provided.

        :param module:
            The module name.
        :params key:
            The configuration key.
        :param default:
            Default value to return if the key doesn't exist.
        :returns:
            A module configuration.
        """
        module_dict = self.__getitem__(module)

        if key is None:
            return module_dict

        return module_dict.get(key, default)


class SubConfig(dict):
    def __init__(self, module, values=None):
        dict.__init__(self, values or ())
        self.module = module

    def __getitem__(self, key):
        try:
            value = dict.__getitem__(self, key)
        except KeyError:
            raise KeyError('Module %r does not have the config key %r' %
                (self.module, key))

        if value is REQUIRED_VALUE:
            raise KeyError('Module %r requires the config key %r to be '
                'set.' % (self.module, key))

        return value

    def get(self, key, default=None):
        if key not in self:
            value = default
        else:
            value = dict.__getitem__(self, key)

        if value is REQUIRED_VALUE:
            raise KeyError('Module %r requires the config key %r to be '
                'set.' % (self.module, key))

        return value


class BaseRoute(object):
    """Interface for URL routes. Custom routes must implement some or all
    methods and attributes from this class.
    """
    #: The regex template.
    template = None
    #: Route name, used to build URLs.
    name = None
    #: True if this route is only used for URL generation and never matches.
    build_only = False
    #: The handler callable or callable in dotted notation.
    handler = None
    #: The custom handler method.
    handler_method = None

    def match(self, request):
        """Matches this route against the current request.

        :param request:
            A :class:`Request` instance.
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

    @cached_property
    def regex(self):
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
            return match.groups(), {}

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
    handler_method = None
    defaults = None

    # Lazy properties.
    regex = None
    reverse_template = None
    variables = None
    has_positional_variables = False

    def __init__(self, template, handler=None, name=None, defaults=None,
        build_only=False, handler_method=None):
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
        :param handler_method:
            A custom handler method to be used.
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
        # If a handler string has a colon, we take it as the method from a
        # handler class, e.g., 'my_module.MyClass:my_method', and store it
        # in the route as 'handler_method'. Not every route mapping to a class
        # must define a method (the request method is used by default), and for
        # functions 'handler_method' is of course always None.
        self.handler_method = handler_method
        if isinstance(handler, basestring) and handler.rfind(':') != -1:
            if handler_method:
                raise BadArgumentError(
                    "If handler_method is defined in a Route, handler "
                    "can't have a colon (got %r)." % handler)
            else:
                self.handler, self.handler_method = handler.rsplit(':', 1)

    @cached_property
    def regex(self):
        variables = {}
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
            variables[name] = re.compile('^%s$' % expr)

        regex = '^%s%s$' % (regex, re.escape(self.template[last:]))
        self.variables = variables
        self.reverse_template = reverse_template + self.template[last:]
        self.has_positional_variables = count > 0
        return re.compile(regex)

    def match(self, request):
        """Matches this route against the current request.

        .. seealso:: :meth:`BaseRoute.match`.
        """
        match = self.regex.match(request.path)
        if match:
            kwargs = self.defaults.copy()
            kwargs.update(match.groupdict())
            if kwargs and self.has_positional_variables:
                args = tuple(value[1] for value in sorted((int(key[2:-2]), \
                    kwargs.pop(key)) for key in \
                    kwargs.keys() if key.startswith('__')))
            else:
                args = ()

            return args, kwargs

    def build(self, request, args, kwargs):
        """Builds a URL for this route.

        .. seealso:: :meth:`Router.build`.
        """
        scheme = kwargs.pop('_scheme', None)
        netloc = kwargs.pop('_netloc', None)
        anchor = kwargs.pop('_anchor', None)
        full = kwargs.pop('_full', False) and not scheme and not netloc

        if full or scheme or netloc:
            netloc = netloc or request.host
            scheme = scheme or 'http'

        path, query = self._build(args, kwargs)
        return urlunsplit(scheme, netloc, path, query, anchor)

    def _build(self, args, kwargs):
        """Builds the path for this route.

        :returns:
            A tuple ``(path, kwargs)`` with the built URL path and extra
            keywords to be used as URL query arguments.
        """
        # Access self.regex just to set the lazy properties.
        regex = self.regex
        variables = self.variables
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
            A :class:`Request` instance.
        :returns:
            A tuple ``(route, args, kwargs)`` if a route matched, or None.
        """
        for route in self.match_routes:
            match = route.match(request)
            if match:
                return route, match[0], match[1]

    def dispatch(self, request, response):
        """Dispatches a request. This calls the :class:`RequestHandler` from
        the matched :class:`Route`.

        :param request:
            A :class:`Request` instance.
        :param response:
            A :class:`Response` instance.
        :raises:
            ``webob.exc.HTTPNotFound`` if no route matched.
        """
        match = self.match(request)
        if not match:
            raise webob.exc.HTTPNotFound()

        request.route, request.route_args, request.route_kwargs = match
        route, args, kwargs = match
        handler_spec = route.handler
        if isinstance(handler_spec, basestring):
            if handler_spec not in self._handlers:
                self._handlers[handler_spec] = import_string(handler_spec)

            request.route.handler = handler_spec = self._handlers[handler_spec]

        try:
            # Functions don't like issubclass().
            is_webapp = issubclass(handler_spec, webapp.RequestHandler)
        except TypeError:
            is_webapp = False

        if is_webapp:
            # webapp.RequestHandler: call initialize() and the request method.
            handler = handler_spec()
            handler.initialize(request, response)
            method = getattr(handler, _normalize_method(request.method))
            if not method:
                # 501 Not Implemented.
                raise webob.exc.HTTPNotImplemented()
            method(*args, **kwargs)
        else:
            # A function or webapp2.RequestHandler: just call it.
            handler_spec(request, response)

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


class RequestContext(object):
    """Sets and releases the request context during a request."""

    def __init__(self, app, environ):
        """Initializes the request context.

        :param app:
            An :class:`WSGIApplication` instance.
        :param environ:
            A WSGI environment.
        """
        self.app = app
        self.environ = environ

    def __enter__(self):
        """Enters the request context.

        :returns:
            A :class:`Request` instance.
        """
        # The active request.
        request = self.app.request_class(self.environ)
        # Make the app available thorugh the request object.
        request.app = self.app
        # The active response.
        response = self.app.response_class()
        # Register global variables.
        self.app.set_globals(app=self.app, request=request)
        return request, response

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the request context.

        This release the context locals except if an exception is caught
        in debug mode. In this case the locals are kept to be inspected.
        """
        if exc_type is None or not self.app.debug:
            self.app.set_globals(app=None, request=None)


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
    #: Allowed request methods.
    allowed_methods = ('GET', 'POST', 'HEAD', 'OPTIONS', 'PUT',
        'DELETE', 'TRACE')
    #: Default class used for the request object.
    request_class = Request
    #: Default class used for the response object.
    response_class = Response
    #: Default class used for the router object.
    router_class = Router
    #: Default class used for the config object.
    config_class = Config
    #: Context class used when a request comes in.
    request_context_class = RequestContext
    #: Global variables.
    app = None
    request = None
    #: Same as app, for compatibility with webapp.
    active_instance = None

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
        # Register global variables.
        self.set_globals(app=self)

    def set_globals(self, app=None, request=None):
        """Registers the global variables for app and request.

        App Engine doesn't have threading, so we just assign them directly.
        For a threaded environment, direct assignment must be replaced by
        assigning to a proxy object that returns app and request using
        thread locals.
        """
        cls = WSGIApplication
        cls.app = cls.active_instance = app
        cls.request = request

    def __call__(self, environ, start_response):
        """Called by WSGI when a request comes in. Calls :meth:`dispatch`."""
        return self.dispatch(environ, start_response)

    def dispatch(self, environ, start_response):
        """This is the actual WSGI application.  This is not implemented in
        :meth:`__call__` so that middlewares can be applied without losing a
        reference to the class. So instead of doing this::

            app = MyMiddleware(app)

        It's a better idea to do this instead::

            app.dispatch = MyMiddleware(app.dispatch)

        Then you still have the original application object around and
        can continue to call methods on it.

        This idea comes from `Flask`_.

        :param environ:
            A WSGI environment.
        :param start_response:
            A callable accepting a status code, a list of headers and an
            optional exception context to start the response.
        """
        with self.request_context_class(self, environ) as context:
            request, response = context
            try:
                if request.method not in self.allowed_methods:
                    # 501 Not Implemented.
                    raise webob.exc.HTTPNotImplemented()

                self.router.dispatch(request, response)
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

            return response(environ, start_response)

    def handle_exception(self, request, response, e):
        """Handles an exception. To set app-wide error handlers, define them
        using the corresponent HTTP status code in the ``error_handlers``
        dictionary of :class:`WSGIApplication`. For example, to set a custom
        `Not Found` page::

            def handle_404(request, response, exception):
                response.out.write('Oops! I could swear this page was here!')
                response.set_status(404)

            app = WSGIApplication([
                (r'/', MyHandler),
            ])
            app.error_handlers[404] = handle_404

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
            A :class:`Request` instance.
        :param response:
            A :class:`Response` instance.
        :param e:
            The raised exception.
        """
        if isinstance(e, HTTPException):
            code = e.code
        else:
            code = 500

        error_handler = self.error_handlers.get(code)
        if error_handler:
            # Handle the exception using a custom handler.
            handler = error_handler(request, response, e)
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

        .. seealso:: :meth:`Config.get_config`.
        """
        return self.config.get_config(module, key=key, default=default)

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
        path = urllib.quote(to_utf8(path))

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


def _normalize_method(method):
    return method.lower().replace('-', '_')


Request.ResponseClass = Response
Response.RequestClass = Request
