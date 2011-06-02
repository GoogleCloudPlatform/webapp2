# -*- coding: utf-8 -*-
"""
    webapp2_extras.routes
    =====================

    Extra route classes for webapp2.

    :copyright: 2011 by tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
import re

import webapp2


class MultiRoute(object):
    """Base class for routes with nested routes."""

    def __init__(self, routes):
        self.routes = []
        # Extract all nested routes.
        for route in routes:
            for r in route.get_routes():
                self.routes.append(r)

    def get_routes(self):
        for route in self.routes:
            yield route

    def get_match_routes(self):
        for route in self.routes:
            if not route.build_only:
                yield route

    def get_build_routes(self):
        for route in self.routes:
            if route.name is not None:
                yield route


class DomainRoute(MultiRoute):
    """A route used to restrict route matches to a given domain or subdomain.

    For example, to restrict routes to a subdomain of the appspot domain::

        app = WSGIApplication([
            DomainRoute('<subdomain>.app-id.appspot.com', [
                Route('/foo', 'FooHandler', 'subdomain-thing'),
            ]),
            Route('/bar', 'BarHandler', 'normal-thing'),
        ])

    The template follows the same syntax used by :class:`webapp2.Route` and
    must define named groups if any value must be added to the match results.
    In the example above, an extra `subdomain` keyword is passed to the handler,
    but if the regex didn't define any named groups, nothing would be added.
    """

    def __init__(self, template, routes):
        """Initializes a URL route.

        :param template:
            A route template to match against ``environ['SERVER_NAME']``.
            See a syntax description in :meth:`webapp2.Route.__init__`.
        :param routes:
            A list of :class:`webapp2.Route` instances.
        """
        super(DomainRoute, self).__init__(routes)
        self.template = template
        self.match_routes = [r for r in self.routes if not r.build_only]

    def get_match_routes(self):
        # This route will do pre-matching before matching the nested routes!
        yield self

    def match(self, request):
        # Use SERVER_NAME to ignore port number that comes with request.host.
        # host_match = self.regex.match(request.host)
        host_match = self.regex.match(request.environ['SERVER_NAME'])
        if host_match:
            for route in self.match_routes:
                match = route.match(request)
                if match:
                    match[2].update(host_match.groupdict())
                    return match

    @webapp2.cached_property
    def regex(self):
        pattern = ''
        last = 0
        template = self.template
        for match in webapp2._ROUTE_REGEX.finditer(template):
            part = template[last:match.start()]
            name = match.group(1)
            expr = match.group(2) or '[^\.]+'
            last = match.end()

            if name:
                pattern += '%s(?P<%s>%s)' % (re.escape(part), name, expr)
            else:
                pattern += '%s%s' % (re.escape(part), expr)

        return re.compile('^%s%s$' % (pattern, re.escape(template[last:])))


class PathPrefixRoute(MultiRoute):
    """The idea of this route is to set a base path for other routes::

        app = WSGIApplication([
            PathPrefixRoute('/users/<user:\w+>', [
                Route('/', UserOverviewHandler, 'user-overview'),
                Route('/profile', UserProfileHandler, 'user-profile'),
                Route('/projects', UserProjectsHandler, 'user-projects'),
            ]),
        ])

    The example above is the same as setting the following routes, just more
    convenient as you can reuse the path prefix::

        app = WSGIApplication([
            Route('/users/<user:\w+>/', UserOverviewHandler, 'user-overview'),
            Route('/users/<user:\w+>/profile', UserProfileHandler, 'user-profile'),
            Route('/users/<user:\w+>/projects', UserProjectsHandler, 'user-projects'),
        ])
    """

    _attr = 'template'

    def __init__(self, prefix, routes):
        """Initializes a URL route.

        :param prefix:
            The path prefix.
        :param routes:
            A list of :class:`webapp2.Route` instances.
        """
        self.prefix = prefix
        self.routes = []
        # Extract all nested routes, prepending a prefix to a route attribute.
        for route in routes:
            for r in route.get_routes():
                setattr(r, self._attr, prefix + getattr(r, self._attr))
                self.routes.append(r)


class NamePrefixRoute(PathPrefixRoute):
    """Same as :class:`PathPrefixRoute`, but prefixes the route name."""

    _attr = 'name'


class HandlerPrefixRoute(PathPrefixRoute):
    """Same as :class:`PathPrefixRoute`, but prefixes the route handler."""

    _attr = 'handler'


class RedirectRoute(webapp2.Route):
    """A convenience route class for easy redirects.

    It adds redirect_to, redirect_to_name and strict_slash options to
    :class:`webapp2.Route`.
    """

    def __init__(self, template, handler=None, name=None, defaults=None,
                 build_only=False, handler_method=None, methods=None,
                 redirect_to=None, redirect_to_name=None, strict_slash=False):
        """Initializes a URL route. Extra arguments compared to
        :meth:`webapp2.Route.__init__`:

        :param redirect_to:
            A URL string or a callable that returns a URL. If set, this route
            is used to redirect to it. The callable is called passing
            ``(handler, *args, **kwargs)`` as arguments. This is a
            convenience to use :class:`RedirectHandler`. These two are
            equivalent::

                route = Route('/foo', handler=webapp2.RedirectHandler, defaults={'_uri': '/bar'})
                route = Route('/foo', redirect_to='/bar')

        :param redirect_to_name:
            Same as `redirect_to`, but the value is the name of a route to
            redirect to. In the example below, accessing '/hello-again' will
            redirect to the route named 'hello'::

                route = Route('/hello', handler=HelloHandler, name='hello')
                route = Route('/hello-again', redirect_to_name='hello')

        :param strict_slash:
            If True, redirects access to the same URL with different trailing
            slash to the strict path defined in the rule. For example, take
            these rules::

                route = Route('/foo', FooHandler, strict_slash=True)
                route = Route('/bar/', BarHandler, strict_slash=True)

            Because **strict_slash** is True, this is what will happen:

            - Access to ``/foo`` will execute ``FooHandler`` normally.
            - Access to ``/bar/`` will execute ``BarHandler`` normally.
            - Access to ``/foo/`` will redirect to ``/foo``.
            - Access to ``/bar`` will redirect to ``/bar/``.
        """
        super(RedirectRoute, self).__init__(
            template, handler=handler, name=name, defaults=defaults,
            build_only=build_only, handler_method=handler_method,
            methods=methods)

        if strict_slash and not name:
            raise ValueError('Routes with strict_slash must have a name.')

        self.strict_slash = strict_slash
        self.redirect_to_name = redirect_to_name

        if redirect_to is not None:
            assert redirect_to_name is None
            self.handler = webapp2.RedirectHandler
            self.defaults['_uri'] = redirect_to

    def get_match_routes(self):
        """Generator to get all routes that can be matched from a route.

        :yields:
            This route or all nested routes that can be matched.
        """
        if self.redirect_to_name:
            main_route = self._get_redirect_route(name=self.redirect_to_name)
        else:
            main_route = self

        if not self.build_only:
            if self.strict_slash is True:
                if self.template.endswith('/'):
                    template = self.template[:-1]
                else:
                    template = self.template + '/'

                yield main_route
                yield self._get_redirect_route(template=template)
            else:
                yield main_route
        elif not self.name:
            raise ValueError("Route %r is build_only but doesn't have a "
                "name" % self)

    def _get_redirect_route(self, template=None, name=None):
        template = template or self.template
        name = name or self.name
        defaults = self.defaults.copy()
        defaults.update({
            '_uri': self._redirect,
            '_name': name,
        })
        new_route = webapp2.Route(template, webapp2.RedirectHandler,
                                  defaults=defaults)
        return new_route

    def _redirect(self, handler, *args, **kwargs):
        # Get from request because args is empty if named routes are set.
        args, kwargs = handler.request.route_args, handler.request.route_kwargs
        kwargs.pop('_uri', None)
        kwargs.pop('_code', None)
        return handler.uri_for(kwargs.pop('_name'), *args, **kwargs)
