"""
Extra route classes. Proof of concepts for webapp2's routing system.
"""
class PrefixRoute(object):
    """The idea of this route is to set a base path to mount other routes::

        route = PrefixRoute('/users/<user:\w+>', [
            Route('/', UserOverviewHandler, 'user-overview'),
            Route('/profile', UserProfileHandler, 'user-profile'),
            Route('/projects', UserProjectsHandler, 'user-projects'),
        ])

    The example above is the same as setting the following routes, just more
    convenient as you can reuse the path prefix:

        Route('/users/<user:\w+>/', UserOverviewHandler, 'user-overview')
        Route('/users/<user:\w+>/profile', UserProfileHandler, 'user-profile')
        Route('/users/<user:\w+>/projects', UserProjectsHandler, 'user-projects')
    """
    def __init__(self, prefix, routes):
        self.prefix = prefix
        self._routes = routes
        self.routes = None

    def get_routes(self):
        if self.routes is None:
            self._prepare_routes()

        for route in self.routes:
            yield route

    def _prepare_routes(self):
        self.routes = []
        for routes in self._routes:
            for route in routes.get_routes():
                route = route.copy()
                route.template = self.prefix + route.template
                self.routes.append(route)
