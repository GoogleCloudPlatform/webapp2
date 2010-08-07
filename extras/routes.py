"""
Extra route classes. Proof of concepts for webapp2's routing system.
"""
import re


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
