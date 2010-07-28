import cgi
import logging
import re
import sys
import traceback
import urlparse
from wsgiref.handlers import CGIHandler

from google.appengine.ext import webapp

import webob

# Allowed request methods.
ALLOWED_METHODS = frozenset(['get', 'post', 'head', 'options', 'put', 'delete',
    'trace'])

url_regex = re.compile(r'''
    \{            # The exact character "{"
    (\w+)         # The variable name (restricted to a-z, 0-9, _)
    (?::([^}]+))? # The optional :regex part
    \}            # The exact character "}"
    ''', re.VERBOSE)


class Response(webob.Response):
    """Abstraction for an HTTP response.

    Implements ``webapp.Response`` interface, except ``wsgi_write()``.

    Properties:
        out: file pointer for the output stream
        headers: wsgiref.headers.Headers instance representing the output headers
    """
    def __init__(self, *args, **kwargs):
        super(Response, self).__init__(*args, **kwargs)

        # webapp uses self.response.out.write(...)
        self.out = self.body_file

    def set_status(self, code, message=None):
        """Sets the HTTP status code of this response.

        Args:
          message: the HTTP status string to use

        If no status string is given, we use the default from the HTTP/1.1
        specification.
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

        Args:
            code: the HTTP code for which we want a message
        """
        message = webob.statusreasons.status_reasons.get(code, None)
        if not message:
            raise Error('Invalid HTTP status code: %d' % code)

        return message


class RequestHandler(object):
    """Our base HTTP request handler. Clients should subclass this class.

    Subclasses should override get(), post(), head(), options(), etc to handle
    different HTTP methods.
    """
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

    def __init__(self, app, request, response):
        self.app = app
        self.request = request
        self.response = response

    def dispatch(self, *args, **kwargs):
        """Dispatches the requested method. If plugins are set, executes
        ``before_dispatch()`` and ``after_dispatch()`` plugin hooks.
        """
        method = getattr(self, args[0], None)
        if method is None:
            return self.error(405)

        if not self.plugins:
            # No plugins are set: just execute the method.
            return method(**kwargs)

        # Execute before_dispatch plugins.
        for plugin in self.plugins:
            hook = getattr(plugin, 'before_dispatch', None)
            if hook:
                rv = hook(self)
                if rv is False:
                    break
        else:
            # Execute the requested method.
            method(**kwargs)

        # Execute after_dispatch plugins.
        for plugin in reversed(self.plugins):
            hook = getattr(plugin, 'after_dispatch', None)
            if hook:
                rv = hook(self)
                if rv is False:
                    break

    def get(self, **kwargs):
        """Handler method for GET requests."""
        self.error(405)

    def post(self, **kwargs):
        """Handler method for POST requests."""
        self.error(405)

    def head(self, **kwargs):
        """Handler method for HEAD requests."""
        self.error(405)

    def options(self, **kwargs):
        """Handler method for OPTIONS requests."""
        self.error(405)

    def put(self, **kwargs):
        """Handler method for PUT requests."""
        self.error(405)

    def delete(self, **kwargs):
        """Handler method for DELETE requests."""
        self.error(405)

    def trace(self, **kwargs):
        """Handler method for TRACE requests."""
        self.error(405)

    def error(self, code):
        """Clears the response output stream and sets the given HTTP error code.

        Args:
            code: the HTTP status error code (e.g., 501)
        """
        self.response.set_status(code)
        self.response.clear()

    def redirect(self, uri, permanent=False):
        """Issues an HTTP redirect to the given relative URL.

        Args:
            uri: a relative or absolute URI (e.g., '../flowers.html')
            permanent: if true, we use a 301 redirect instead of a 302 redirect
        """
        if permanent:
            self.response.set_status(301)
        else:
            self.response.set_status(302)

        absolute_url = urlparse.urljoin(self.request.uri, uri)
        self.response.headers['Location'] = str(absolute_url)
        self.response.clear()

    def handle_exception(self, exception, debug_mode):
        """Called if this handler throws an exception during execution.

        The default behavior is to call self.error(500) and print a stack trace
        if debug_mode is True.

        Args:
            exception: the exception that was thrown
            debug_mode: True if the web application is running in debug mode
        """
        self.error(500)
        logging.exception(exception)
        if debug_mode:
            #raise
            lines = ''.join(traceback.format_exception(*sys.exc_info()))
            self.response.clear()
            self.response.out.write('<pre>%s</pre>' % (cgi.escape(lines,
                quote=True)))

    def url_for(self, name, **kwargs):
        return self.request.environ['router.build'](name, **kwargs)


class WSGIApplication(object):
    """Wraps a set of webapp RequestHandlers in a WSGI-compatible application.

    To use this class, pass a list of (URI regular expression, RequestHandler)
    pairs to the constructor, and pass the class instance to a WSGI handler.
    See the example in the module comments for details.

    The URL mapping is first-match based on the list ordering.
    """
    request_class = webapp.Request
    response_class = Response

    def __init__(self, url_map, debug=False, config=None):
        self.set_router(url_map)
        self.debug = debug

    def __call__(self, environ, start_response):
        """Shortcut for :meth:`WSGIApplication.wsgi_app`."""
        try:
            return self.wsgi_app(environ, start_response)
        except Exception, e:
            logging.exception(e)

    def wsgi_app(self, environ, start_response):
        """Called by WSGI when a request comes in."""
        request = self.request_class(environ)
        response = self.response_class()

        method = environ['REQUEST_METHOD'].lower()
        if method not in ALLOWED_METHODS:
            # TODO raise exception: 405 Method Not Allowed
            pass

        handler_class, kwargs = self.match_url(request)

        if handler_class:
            handler = handler_class(self, request, response)
            try:
                handler.dispatch(method, **kwargs)
            except Exception, e:
                # TODO handle exception
                handler.handle_exception(e, self.debug)
        else:
            response.set_status(404)

        return response(environ, start_response)

    def set_router(self, url_map):
        self.router = Router()
        for spec in url_map:
            if len(spec) == 3:
                self.router.add(*spec)
            elif len(spec) == 4:
                self.router.add(*spec[:3], **spec[3])

    def match_url(self, request):
        res = self.router.match(request.path)
        request.environ['router.route'] = res
        request.environ['router.build'] = self.router.build
        if not res:
            return (None, None)

        return res[0].handler, res[1]

    def handle_exception(self, e):
        pass


class Route(object):
    def __init__(self, path, handler, **defaults):
        self.path = path
        self.handler = handler
        self.defaults = defaults
        self.variables = []

        last = 0
        regex = ''
        template = ''
        for match in url_regex.finditer(path):
            part = path[last:match.start()]
            name = match.group(1)
            expr = match.group(2) or '[^/]+'
            last = match.end()

            regex += re.escape(part) + '(?P<%s>%s)' % (name, expr)
            template += '%s%%(%s)s' % (part, name)
            self.variables.append(name)

        self.template = template + path[last:]
        self.regex = re.compile('^%s$' % (regex + re.escape(path[last:]),))

    def match(self, path):
        match = self.regex.match(path)
        if match:
            values = self.defaults.copy()
            values.update(match.groupdict())
            return (self, values)

    def build(self, **kwargs):
        values = self.defaults.copy()
        values.update((str(k), str(v)) for k, v in kwargs.iteritems())
        try:
            res = self.template % values
        except KeyError, e:
            # TODO
            raise

        return res


class Router(object):
    def __init__(self):
        self.routes = []
        self.route_names = {}

    def add(self, path, name, handler, **defaults):
        route = Route(path, handler, **defaults)
        self.routes.append(route)
        self.route_names[name] = route

    def match(self, path):
        for route in self.routes:
            match = route.match(path)
            if match:
                return match

    def build(self, name, _full=False, _anchor=None, **kwargs):
        # TODO:
        # url encode values
        # append extra values as arguments: ?foo=bar&baz=ding
        # build full urls
        # add encoded anchor
        route = self.route_names.get(name, None)
        if not route:
            raise KeyError('Route %s is not defined.' % name)

        return route.build(**kwargs)


def run_wsgi_app(app):
    CGIHandler().run(app)
