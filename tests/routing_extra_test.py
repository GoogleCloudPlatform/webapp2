# -*- coding: utf-8 -*-
import webapp2

from webapp2_extras.routes import (DomainRoute, HandlerPrefixRoute,
    RedirectRoute, NamePrefixRoute, PathPrefixRoute)

import test_base


class HomeHandler(webapp2.RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('home sweet home')


app = webapp2.WSGIApplication([
    #RedirectRoute('/', name='home', handler=HomeHandler),
    RedirectRoute('/redirect-me-easily', redirect_to='/i-was-redirected-easily'),
    RedirectRoute('/redirect-me-easily2', redirect_to='/i-was-redirected-easily', defaults={'_code': 302}),
    RedirectRoute('/redirect-me-easily3', redirect_to='/i-was-redirected-easily', defaults={'_permanent': False}),
    RedirectRoute('/strict-foo', HomeHandler, 'foo-strict', strict_slash=True),
    RedirectRoute('/strict-bar/', HomeHandler, 'bar-strict', strict_slash=True),
    RedirectRoute('/redirect-to-name-destination', name='redirect-to-name-destination', handler=HomeHandler),
    RedirectRoute('/redirect-to-name', redirect_to_name='redirect-to-name-destination'),
], debug=True)


class TestRedirectRoute(test_base.BaseTestCase):
    def test_route_redirect_to(self):
        route = RedirectRoute('/foo', redirect_to='/bar')
        router = webapp2.Router(None, [route])
        route_match, args, kwargs = router.match(webapp2.Request.blank('/foo'))
        self.assertEqual(route_match, route)
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {'_uri': '/bar'})

    def test_easy_redirect_to(self):
        req = webapp2.Request.blank('/redirect-me-easily')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '301 Moved Permanently')
        self.assertEqual(rsp.body, '')
        self.assertEqual(rsp.headers['Location'], 'http://localhost/i-was-redirected-easily')

        req = webapp2.Request.blank('/redirect-me-easily2')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '302 Found')
        self.assertEqual(rsp.body, '')
        self.assertEqual(rsp.headers['Location'], 'http://localhost/i-was-redirected-easily')

        req = webapp2.Request.blank('/redirect-me-easily3')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '302 Found')
        self.assertEqual(rsp.body, '')
        self.assertEqual(rsp.headers['Location'], 'http://localhost/i-was-redirected-easily')

    def test_redirect_to_name(self):
        req = webapp2.Request.blank('/redirect-to-name')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '301 Moved Permanently')
        self.assertEqual(rsp.body, '')
        self.assertEqual(rsp.headers['Location'], 'http://localhost/redirect-to-name-destination')

    def test_strict_slash(self):
        req = webapp2.Request.blank('/strict-foo')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.body, 'home sweet home')

        req = webapp2.Request.blank('/strict-bar/')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.body, 'home sweet home')

        # Now the non-strict...

        req = webapp2.Request.blank('/strict-foo/')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '301 Moved Permanently')
        self.assertEqual(rsp.body, '')
        self.assertEqual(rsp.headers['Location'], 'http://localhost/strict-foo')

        req = webapp2.Request.blank('/strict-bar')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '301 Moved Permanently')
        self.assertEqual(rsp.body, '')
        self.assertEqual(rsp.headers['Location'], 'http://localhost/strict-bar/')

        # Strict slash routes must have a name.

        self.assertRaises(ValueError, RedirectRoute, '/strict-bar/', handler=HomeHandler, strict_slash=True)

    def test_build_only(self):
        r = RedirectRoute('/', handler=HomeHandler, build_only=True)
        self.assertRaises(ValueError, webapp2.Router, None, [r])


class TestPrefixRoutes(test_base.BaseTestCase):
    def test_simple(self):
        router = webapp2.Router(None, [
            PathPrefixRoute('/a', [
                webapp2.Route('/', 'a', 'name-a'),
                webapp2.Route('/b', 'a/b', 'name-a/b'),
                webapp2.Route('/c', 'a/c', 'name-a/c'),
                PathPrefixRoute('/d', [
                    webapp2.Route('/', 'a/d', 'name-a/d'),
                    webapp2.Route('/b', 'a/d/b', 'name-a/d/b'),
                    webapp2.Route('/c', 'a/d/c', 'name-a/d/c'),
                ]),
            ])
        ])

        path = '/a/'
        match = ((), {})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'name-a', match[0], match[1]), path)

        path = '/a/b'
        match = ((), {})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'name-a/b', match[0], match[1]), path)

        path = '/a/c'
        match = ((), {})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'name-a/c', match[0], match[1]), path)

        path = '/a/d/'
        match = ((), {})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'name-a/d', match[0], match[1]), path)

        path = '/a/d/b'
        match = ((), {})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'name-a/d/b', match[0], match[1]), path)

        path = '/a/d/c'
        match = ((), {})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'name-a/d/c', match[0], match[1]), path)

    def test_with_variables_name_and_handler(self):
        router = webapp2.Router(None, [
            PathPrefixRoute('/user/<username:\w+>', [
                HandlerPrefixRoute('apps.users.', [
                    NamePrefixRoute('user-', [
                        webapp2.Route('/', 'UserOverviewHandler', 'overview'),
                        webapp2.Route('/profile', 'UserProfileHandler', 'profile'),
                        webapp2.Route('/projects', 'UserProjectsHandler', 'projects'),
                    ]),
                ]),
            ])
        ])

        path = '/user/calvin/'
        match = ((), {'username': 'calvin'})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'user-overview', match[0], match[1]), path)

        path = '/user/calvin/profile'
        match = ((), {'username': 'calvin'})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'user-profile', match[0], match[1]), path)

        path = '/user/calvin/projects'
        match = ((), {'username': 'calvin'})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'user-projects', match[0], match[1]), path)


class TestDomainRoute(test_base.BaseTestCase):
    def test_simple(self):
        router = webapp2.Router(None, [
            DomainRoute('<subdomain>.<:.*>', [
                webapp2.Route('/foo', 'FooHandler', 'subdomain-thingie'),
            ])
        ])

        self.assertRaises(webapp2.exc.HTTPNotFound, router.match, webapp2.Request.blank('/foo'))

        match = router.match(webapp2.Request.blank('http://my-subdomain.app-id.appspot.com/foo'))
        self.assertEqual(match[1:], ((), {'subdomain': 'my-subdomain'}))

        match = router.match(webapp2.Request.blank('http://another-subdomain.app-id.appspot.com/foo'))
        self.assertEqual(match[1:], ((), {'subdomain': 'another-subdomain'}))

        url = router.build(webapp2.Request.blank('/'), 'subdomain-thingie', (), {'_netloc': 'another-subdomain.app-id.appspot.com'})
        self.assertEqual(url, 'http://another-subdomain.app-id.appspot.com/foo')

    def test_with_variables_name_and_handler(self):
        router = webapp2.Router(None, [
            DomainRoute('<subdomain>.<:.*>', [
                PathPrefixRoute('/user/<username:\w+>', [
                    HandlerPrefixRoute('apps.users.', [
                        NamePrefixRoute('user-', [
                            webapp2.Route('/', 'UserOverviewHandler', 'overview'),
                            webapp2.Route('/profile', 'UserProfileHandler', 'profile'),
                            webapp2.Route('/projects', 'UserProjectsHandler', 'projects'),
                        ]),
                    ]),
                ])
            ]),
        ])

        path = 'http://my-subdomain.app-id.appspot.com/user/calvin/'
        match = ((), {'username': 'calvin', 'subdomain': 'my-subdomain'})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        match[1].pop('subdomain')
        match[1]['_netloc'] = 'my-subdomain.app-id.appspot.com'
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'user-overview', match[0], match[1]), path)

        path = 'http://my-subdomain.app-id.appspot.com/user/calvin/profile'
        match = ((), {'username': 'calvin', 'subdomain': 'my-subdomain'})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        match[1].pop('subdomain')
        match[1]['_netloc'] = 'my-subdomain.app-id.appspot.com'
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'user-profile', match[0], match[1]), path)

        path = 'http://my-subdomain.app-id.appspot.com/user/calvin/projects'
        match = ((), {'username': 'calvin', 'subdomain': 'my-subdomain'})
        self.assertEqual(router.match(webapp2.Request.blank(path))[1:], match)
        match[1].pop('subdomain')
        match[1]['_netloc'] = 'my-subdomain.app-id.appspot.com'
        self.assertEqual(router.build(webapp2.Request.blank('/'), 'user-projects', match[0], match[1]), path)


if __name__ == '__main__':
    test_base.main()
