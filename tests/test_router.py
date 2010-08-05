# -*- coding: utf-8 -*-
"""
Tests for webapp2 router
"""
import random
import unittest

from webapp2 import Request, Route, Router


class TestRoute(unittest.TestCase):
    def test_no_variable(self):
        route = Route(r'/hello', None)
        handler, args, kwargs = route.match(Request.blank('/hello'))
        self.assertEqual(kwargs, {})
        url = route.build(Request.blank('/'), (), {})
        self.assertEqual(url, '/hello')

        route = Route(r'/hello/world/', None)
        handler, args, kwargs = route.match(Request.blank('/hello/world/'))
        self.assertEqual(kwargs, {})
        url = route.build(Request.blank('/'), (), {})
        self.assertEqual(url, '/hello/world/')

    def test_repetition_operator(self):
        route = Route(r'/<:\d>', None)
        self.assertEqual(route.match(Request.blank('/1')), (None, ('1',), {}))
        self.assertEqual(route.match(Request.blank('/2')), (None, ('2',), {}))

        route = Route(r'/<:\d{2,3}>', None)
        self.assertEqual(route.match(Request.blank('/11')), (None, ('11',), {}))
        self.assertEqual(route.match(Request.blank('/111')), (None, ('111',), {}))
        self.assertEqual(route.match(Request.blank('/1111')), None)

    def test_unnamed_variable(self):
        route = Route(r'/<:\d{4}>', None)
        self.assertEqual(route.match(Request.blank('/2010')), (None, ('2010',), {}))
        self.assertEqual(route.match(Request.blank('/aaaa')), None)

        route = Route(r'/<:\d{2}>.<:\d{2}>', None)
        self.assertEqual(route.match(Request.blank('/98.99')), (None, ('98', '99'), {}))
        self.assertEqual(route.match(Request.blank('/aa.aa')), None)

        route = Route(r'/<:\d{2}>.<:\d{2}>/<foo>', None)
        self.assertEqual(route.match(Request.blank('/98.99/test')), (None, ('98', '99'), {'foo': 'test'}))
        self.assertEqual(route.match(Request.blank('/aa.aa/test')), None)

    def test_simple_variable(self):
        route = Route(r'/<foo>', None)
        self.assertEqual(route.match(Request.blank('/bar')), (None, (), {'foo': 'bar'}))
        url = route.build(Request.blank('/'), (), dict(foo='baz'))
        self.assertEqual(url, '/baz')

    def test_expr_variable(self):
        route = Route(r'/<year:\d{4}>', None)
        self.assertEqual(route.match(Request.blank('/bar')), None)
        self.assertEqual(route.match(Request.blank('/2010')), (None, (), {'year': '2010'}))
        self.assertEqual(route.match(Request.blank('/1900')), (None, (), {'year': '1900'}))
        url = route.build(Request.blank('/'), (), dict(year='2010'))
        self.assertEqual(url, '/2010')

    def test_expr_variable2(self):
        route = Route(r'/<year:\d{4}>/foo/', None)
        url = route.build(Request.blank('/'), (), dict(year='2010'))
        self.assertEqual(url, '/2010/foo/')

    def test_build_missing_argument(self):
        route = Route(r'/<:\d{4}>', None)
        self.assertRaises(TypeError, route.build)
        self.assertRaises(TypeError, route.build, Request.blank('/'), (2010,))

    def test_build_invalid_argument(self):
        route = Route(r'/<:\d{4}>', None)
        self.assertRaises(ValueError, route.build, Request.blank('/'), ('20100',), {})

    def test_build_invalid_argument2(self):
        route = Route(r'/<:\d{4}>', None)
        self.assertRaises(ValueError, route.build, Request.blank('/'), ('201a',), {})

    def test_build_missing_keyword(self):
        route = Route(r'/<year:\d{4}>', None)
        self.assertRaises(KeyError, route.build, Request.blank('/'), (), {})

    def test_build_missing_keyword2(self):
        route = Route(r'/<year:\d{4}>/<month:\d{2}>', None)
        self.assertRaises(KeyError, route.build, Request.blank('/'), (), dict(year='2010'))

    def test_build_invalid_keyword(self):
        route = Route(r'/<year:\d{4}>', None)
        self.assertRaises(ValueError, route.build, Request.blank('/'), (), dict(year='20100'))

    def test_build_invalid_keyword2(self):
        route = Route(r'/<year:\d{4}>', None)
        self.assertRaises(ValueError, route.build, Request.blank('/'), (), dict(year='201a'))

    def test_build_with_unnamed_variable(self):
        route = Route(r'/<:\d{4}>/<month:\d{2}>', None)

        url = route.build(Request.blank('/'), (2010,), dict(month=10))
        self.assertEqual(url, '/2010/10')

        url = route.build(Request.blank('/'), ('1999',), dict(month='07'))
        self.assertEqual(url, '/1999/07')

    def test_build_default_keyword(self):
        route = Route(r'/<year:\d{4}>/<month:\d{2}>', None,
            defaults={'month': 10})
        url = route.build(Request.blank('/'), (), dict(year='2010'))
        self.assertEqual(url, '/2010/10')

        route = Route(r'/<year:\d{4}>/<month:\d{2}>', None,
            defaults={'year': 1900})
        url = route.build(Request.blank('/'), (), dict(month='07'))
        self.assertEqual(url, '/1900/07')

    def test_build_extra_keyword(self):
        route = Route(r'/<year:\d{4}>', None)
        url = route.build(Request.blank('/'), (), dict(year='2010', foo='bar'))
        self.assertEqual(url, '/2010?foo=bar')
        # Arguments are sorted.
        url = route.build(Request.blank('/'), (), dict(year='2010', foo='bar', baz='ding'))
        self.assertEqual(url, '/2010?baz=ding&foo=bar')

    def test_build_extra_positional_keyword(self):
        route = Route(r'/<year:\d{4}>/<:\d{2}>', None)

        url = route.build(Request.blank('/'), ('08', 'i-should-be-ignored', 'me-too'), dict(year='2010', foo='bar'))
        self.assertEqual(url, '/2010/08?foo=bar')

        url = route.build(Request.blank('/'), ('08', 'i-should-be-ignored', 'me-too'), dict(year='2010', foo='bar', baz='ding'))
        self.assertEqual(url, '/2010/08?baz=ding&foo=bar')

    def test_build_int_keyword(self):
        route = Route(r'/<year:\d{4}>', None)
        url = route.build(Request.blank('/'), (), dict(year=2010))
        self.assertEqual(url, '/2010')

    def test_build_int_variable(self):
        route = Route(r'/<:\d{4}>', None)
        url = route.build(Request.blank('/'), (2010,), {})
        self.assertEqual(url, '/2010')

    def test_router_build_error(self):
        router = Router()
        router.add(Route('/<year:\d{4}>', None, name='year-page'))

        url = router.build('year-page', Request.blank('/'), (), dict(year='2010'))
        self.assertEqual(url, '/2010')

        self.assertRaises(KeyError, router.build, 'i-dont-exist', Request.blank('/'), (), dict(year='2010'))

    def test_reverse_template(self):
        route = Route('/foo', None)
        self.assertEqual(route.reverse_template, '/foo')

        route = Route('/foo/<bar>', None)
        self.assertEqual(route.reverse_template, '/foo/%(bar)s')

        route = Route('/foo/<bar>/<baz:\d>', None)
        self.assertEqual(route.reverse_template, '/foo/%(bar)s/%(baz)s')

    def test_invalid_template(self):
        # To break it:
        # <>foo:><bar<:baz>
        route = Route('/<foo/<:bar', None)
        self.assertEqual(route.reverse_template, '/<foo/<:bar')

    def test_build_full_without_request(self):
        router = Router()
        router.add(Route(r'/hello', None, name='hello'))
        self.assertRaises(AttributeError, router.build, 'hello', None, (), dict(_full=True))
        self.assertRaises(AttributeError, router.build, 'hello', None, (), dict(_scheme='https'))

    def test_positions(self):
        template = '/<:\d+>' * 98
        args = tuple(str(i) for i in range(98))
        url_res = '/' + '/'.join(args)

        route = Route(template, None)
        self.assertEqual(route.match(Request.blank(url_res)), (None, args, {}))
        url = route.build(Request.blank('/'), args, {})
        self.assertEqual(url_res, url)

        args = [str(i) for i in range(1000)]
        random.shuffle(args)
        args = tuple(args[:98])
        url_res = '/' + '/'.join(args)
        self.assertEqual(route.match(Request.blank(url_res)), (None, args, {}))
        url = route.build(Request.blank('/'), args, {})
        self.assertEqual(url_res, url)

    def test_build_only_without_name(self):
        router = Router()
        self.assertRaises(ValueError, router.add, Route(r'/<foo>', None, build_only=True))

    def test_route_repr(self):
        self.assertEqual(Route(r'/<foo>', None).__repr__(),
            "<Route('/<foo>', None, name=None, defaults={}, build_only=False)>")
        self.assertEqual(Route(r'/<foo>', None, name='bar', defaults={'baz': 'ding'}, build_only=True).__repr__(),
            "<Route('/<foo>', None, name='bar', defaults={'baz': 'ding'}, build_only=True)>")

        self.assertEqual(str(Route(r'/<foo>', None)),
            "<Route('/<foo>', None, name=None, defaults={}, build_only=False)>")
        self.assertEqual(str(Route(r'/<foo>', None, name='bar', defaults={'baz': 'ding'}, build_only=True)),
            "<Route('/<foo>', None, name='bar', defaults={'baz': 'ding'}, build_only=True)>")

    def test_router_repr(self):
        router = Router()
        router.add(Route(r'/hello', None, name='hello', build_only=True))
        router.add(Route(r'/world', None))

        self.assertEqual(router.__repr__(), "<Router([<Route('/world', None, name=None, defaults={}, build_only=False)>, <Route('/hello', None, name='hello', defaults={}, build_only=True)>])>")
