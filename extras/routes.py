"""
Extra route classes. Proof of concepts for webapp2's routing system.
"""
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
