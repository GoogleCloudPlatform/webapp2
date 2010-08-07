"""
Extra route classes. Proof of concepts for webapp2's routing system.
"""
from webapp2 import Route


class PrefixRoute(object):
    """The idea of this route is to set a base path and name for other routes::

        route = PrefixRoute('/users/<user:\w+>', [
            Route('/', UserOverviewHandler, 'user-overview'),
            Route('/profile', UserProfileHandler, 'user-profile'),
            Route('/projects', UserProjectsHandler, 'user-projects'),
        ])

    The example above is the same as setting the following routes, just more
    convenient as you can reuse the path and name prefixes::

        Route('/users/<user:\w+>/', UserOverviewHandler, 'user-overview')
        Route('/users/<user:\w+>/profile', UserProfileHandler, 'user-profile')
        Route('/users/<user:\w+>/projects', UserProjectsHandler, 'user-projects')
    """
    prefix_attr = 'template'

    def __init__(self, prefix, routes):
        self.prefix = prefix
        self.routes = routes

    def get_routes(self):
        for routes in self.routes:
            for route in routes.get_routes():
                route = route.copy()
                setattr(route, self.prefix_attr, self.prefix + getattr(route,
                    self.prefix_attr))

                yield route


class NamePrefixRoute(PrefixRoute):
    """Same as :class:`PrefixRoute`, but prefixes the names of routes."""
    prefix_attr = 'name'


class HandlerPrefixRoute(PrefixRoute):
    """Same as :class:`PrefixRoute`, but prefixes the handlers of routes."""
    prefix_attr = 'handler'
