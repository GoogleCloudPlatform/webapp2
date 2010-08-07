"""
Extra route classes. Proof of concepts for webapp2's routing system.
"""
import re

import webapp2


class Route(webapp2.Route):
    """An improved route class that adds redirect_to and strict_slash options.
    """
    def __init__(self, template, handler=None, name=None, defaults=None,
        build_only=False, redirect_to=None, strict_slash=False):
        """Initializes a URL route. Extra arguments:

        :param redirect_to:
            If set, this route is used to redirect to a URL. The value can be
            a URL string or a callable that returns a URL. The callable is
            called passing ``(handler, *args, **kwargs)`` as arguments. This is
            a convenience to use :class:`RedirectHandler`. These two are
            equivalent::

                route = Route('/foo', RedirectHandler, defaults={'url': '/bar'})
                route = Route('/foo', redirect_to='/bar')
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
        super(Route, self).__init__(template, handler, name, defaults,
            build_only)

        if strict_slash and not name:
            raise ValueError('Routes with strict_slash must have a name.')

        self.strict_slash = strict_slash

        if redirect_to is not None:
            self.handler = webapp2.RedirectHandler
            self.defaults['url'] = redirect_to

    def get_match_routes(self, router):
        """Generator to get all routes that can be matched from a route.

        :yields:
            This route or all nested routes that can be matched.
        """
        if not self.build_only:
            if self.strict_slash is True:
                if self.template.endswith('/'):
                    template = self.template[:-1]
                else:
                    template = self.template + '/'

                defaults = self.defaults.copy()
                defaults.update({
                    'url': self._redirect_to_strict,
                    'route_name': self.name
                })
                new_route = Route(template, webapp2.RedirectHandler,
                    defaults=defaults)
                for route in [self, new_route]:
                    yield route
            else:
                yield self
        elif not self.name:
            raise ValueError("Route %r is build_only but doesn't have a "
                "name" % self)

    def _redirect_to_strict(self, handler, *args, **kwargs):
        return handler.url_for(kwargs.pop('route_name'), *args, **kwargs)


class MultiRoute(object):
    """Base class for routes with nested routes."""
    def __init__(self, routes):
        self._routes = routes
        self.routes = None

    def get_routes(self, router):
        if self.routes is None:
            self._prepare_routes(router)

        for route in self.routes:
            yield route

    def get_match_routes(self, router):
        if self.routes is None:
            self._prepare_routes(router)

        for route in self.routes:
            if not route.build_only:
                yield route

    def get_build_routes(self, router):
        if self.routes is None:
            self._prepare_routes(router)

        for route in self.routes:
            if route.name is not None:
                yield route

    def _prepare_routes(self, router):
        self.routes = []
        for routes in self._routes:
            for route in routes.get_routes(router):
                self.routes.append(route)


class PathPrefixRoute(MultiRoute):
    """The idea of this route is to set a base path for other routes::

        route = PrefixRoute('/users/<user:\w+>', [
            Route('/', UserOverviewHandler, 'user-overview'),
            Route('/profile', UserProfileHandler, 'user-profile'),
            Route('/projects', UserProjectsHandler, 'user-projects'),
        ])

    The example above is the same as setting the following routes, just more
    convenient as you can reuse the path prefix::

        Route('/users/<user:\w+>/', UserOverviewHandler, 'user-overview')
        Route('/users/<user:\w+>/profile', UserProfileHandler, 'user-profile')
        Route('/users/<user:\w+>/projects', UserProjectsHandler, 'user-projects')
    """
    prefix_attr = 'template'

    def __init__(self, prefix, routes):
        super(PathPrefixRoute, self).__init__(routes)
        self.prefix = prefix

    def _prepare_routes(self, router):
        self.routes = []
        for routes in self._routes:
            for route in routes.get_routes(router):
                setattr(route, self.prefix_attr, self.prefix + getattr(route,
                    self.prefix_attr))

                self.routes.append(route)


class NamePrefixRoute(PathPrefixRoute):
    """Same as :class:`PrefixRoute`, but prefixes the names of routes."""
    prefix_attr = 'name'


class HandlerPrefixRoute(PathPrefixRoute):
    """Same as :class:`PrefixRoute`, but prefixes the handlers of routes."""
    prefix_attr = 'handler'


class DomainRoute(MultiRoute):
    """A route used to restrict route matches to a given domain or subdomain.

    For example, to restrict routes to a subdomain of the appspot domain::

        SUBDOMAIN_RE = '^([^.]+)\.app-id\.appspot\.com$'

        router = Router([
            DomainRoute(SUBDOMAIN_RE, [
                Route('/foo', 'FooHandler', 'subdomain-thingie'),
            ])
        ])

    """
    def __init__(self, regex, routes):
        super(DomainRoute, self).__init__(routes)
        self.regex = re.compile(regex)

    def get_match_routes(self, router):
        if self.routes is None:
            self._prepare_routes(router)
            self.routes = [r for r in self.routes if not r.build_only]

        yield self

    def match(self, request):
        # Using SERVER_NAME to ignore port number that comes with request.host
        host_match = self.regex.match(request.environ['SERVER_NAME'])
        if host_match:
            for route in self.routes:
                match = route.match(request)
                if match:
                    handler, args, kwargs = match
                    kwargs['_host_match'] = host_match.groups()

                    return handler, args, kwargs
