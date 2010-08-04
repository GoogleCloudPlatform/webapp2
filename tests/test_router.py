# -*- coding: utf-8 -*-
"""
Tests for webapp2 router
"""
import random
import unittest

from webapp2 import Request, Route, Router


class TestRoute(unittest.TestCase):
    def test_no_variable(self):
        route = Route(r'/hello')
        matched_route, args, kwargs = route.match(Request.blank('/hello'))
        self.assertEqual(matched_route, route)
        self.assertEqual(kwargs, {})
        self.assertEqual(route.build(), '/hello')

        route = Route(r'/hello/world/')
        matched_route, args, kwargs = route.match(Request.blank('/hello/world/'))
        self.assertEqual(matched_route, route)
        self.assertEqual(kwargs, {})
        self.assertEqual(route.build(), '/hello/world/')

    def test_repetition_operator(self):
        route = Route(r'/<:\d>')
        self.assertEqual(route.match(Request.blank('/1')), (route, ('1',), {}))
        self.assertEqual(route.match(Request.blank('/2')), (route, ('2',), {}))

        route = Route(r'/<:\d{2,3}>')
        self.assertEqual(route.match(Request.blank('/11')),
            (route, ('11',), {}))
        self.assertEqual(route.match(Request.blank('/111')), (route,
            ('111',), {}))
        self.assertEqual(route.match(Request.blank('/1111')), None)

    def test_unnamed_variable(self):
        route = Route(r'/<:\d{4}>')
        self.assertEqual(route.match(Request.blank('/2010')), (route,
            ('2010',), {}))
        self.assertEqual(route.match(Request.blank('/aaaa')), None)

        route = Route(r'/<:\d{2}>.<:\d{2}>')
        self.assertEqual(route.match(Request.blank('/98.99')), (route,
            ('98', '99'), {}))
        self.assertEqual(route.match(Request.blank('/aa.aa')), None)

        route = Route(r'/<:\d{2}>.<:\d{2}>/<foo>')
        self.assertEqual(route.match(Request.blank('/98.99/test')),
            (route, ('98', '99'), {'foo': 'test'}))
        self.assertEqual(route.match(Request.blank('/aa.aa/test')), None)

    def test_simple_variable(self):
        route = Route(r'/<foo>')
        self.assertEqual(route.match(Request.blank('/bar')),
            (route, (), {'foo': 'bar'}))
        self.assertEqual(route.build(foo='baz'), '/baz')

    def test_expr_variable(self):
        route = Route(r'/<year:\d{4}>')
        self.assertEqual(route.match(Request.blank('/bar')), None)
        self.assertEqual(route.match(Request.blank('/2010')),
            (route, (), {'year': '2010'}))
        self.assertEqual(route.match(Request.blank('/1900')),
            (route, (), {'year': '1900'}))
        self.assertEqual(route.build(year='2010'), '/2010')

    def test_expr_variable2(self):
        route = Route(r'/<year:\d{4}>/foo/')
        self.assertEqual(route.build(year='2010'), '/2010/foo/')

    def test_build_missing_argument(self):
        route = Route(r'/<:\d{4}>')
        self.assertRaises(KeyError, route.build)

    def test_build_missing_argument2(self):
        route = Route(r'/<:\d{4}>/<:\d{2}>')
        self.assertRaises(KeyError, route.build, 2010)

    def test_build_invalid_argument(self):
        route = Route(r'/<:\d{4}>')
        self.assertRaises(ValueError, route.build, '20100')

    def test_build_invalid_argument2(self):
        route = Route(r'/<:\d{4}>')
        self.assertRaises(ValueError, route.build, '201a')

    def test_build_missing_keyword(self):
        route = Route(r'/<year:\d{4}>')
        self.assertRaises(KeyError, route.build)

    def test_build_missing_keyword2(self):
        route = Route(r'/<year:\d{4}>/<month:\d{2}>')
        self.assertRaises(KeyError, route.build, year='2010')

    def test_build_invalid_keyword(self):
        route = Route(r'/<year:\d{4}>')
        self.assertRaises(ValueError, route.build, year='20100')

    def test_build_invalid_keyword2(self):
        route = Route(r'/<year:\d{4}>')
        self.assertRaises(ValueError, route.build, year='201a')

    def test_build_with_unnamed_variable(self):
        route = Route(r'/<:\d{4}>/<month:\d{2}>')
        self.assertEqual(route.build(2010, month=10), '/2010/10')
        self.assertEqual(route.build('1999', month='07'), '/1999/07')

    def test_build_default_keyword(self):
        route = Route(r'/<year:\d{4}>/<month:\d{2}>',
            defaults={'month': 10})
        self.assertEqual(route.build(year='2010'), '/2010/10')

        route = Route(r'/<year:\d{4}>/<month:\d{2}>',
            defaults={'year': 1900})
        self.assertEqual(route.build(month='07'), '/1900/07')

    def test_build_extra_keyword(self):
        route = Route(r'/<year:\d{4}>')
        self.assertEqual(route.build(year='2010', foo='bar'), '/2010?foo=bar')
        self.assertEqual(route.build(year='2010', foo='bar', baz='ding'),
            '/2010?foo=bar&baz=ding')

    def test_build_extra_positional_keyword(self):
        route = Route(r'/<year:\d{4}>/<:\d{2}>')
        self.assertEqual(route.build('08', 'i-should-be-ignored', 'me-too', year='2010', foo='bar'), '/2010/08?foo=bar')
        self.assertEqual(route.build('08', 'i-should-be-ignored', 'me-too', year='2010', foo='bar', baz='ding'),
            '/2010/08?foo=bar&baz=ding')

    def test_build_int_keyword(self):
        route = Route(r'/<year:\d{4}>')
        self.assertEqual(route.build(year=2010), '/2010')

    def test_build_int_variable(self):
        route = Route(r'/<:\d{4}>')
        self.assertEqual(route.build(2010), '/2010')

    def test_router_build_error(self):
        router = Router()
        router.add(Route('/<year:\d{4}>', name='year-page'), 'my_handler')
        self.assertEqual(router.build('year-page', year='2010'), '/2010')
        self.assertRaises(KeyError, router.build, 'i-dont-exist', year='2010')

    def test_reverse_template(self):
        route = Route('/foo')
        self.assertEqual(route.reverse_template, '/foo')

        route = Route('/foo/<bar>')
        self.assertEqual(route.reverse_template, '/foo/%(bar)s')

        route = Route('/foo/<bar>/<baz:\d>')
        self.assertEqual(route.reverse_template, '/foo/%(bar)s/%(baz)s')

    def test_invalid_template(self):
        # To break it:
        # <>foo:><bar<:baz>
        route = Route('/<foo/<:bar')
        self.assertEqual(route.reverse_template, '/<foo/<:bar')

    def test_build_full_without_request(self):
        router = Router()
        router.add(Route(r'/hello', name='hello'), 'my_handler')
        self.assertRaises(ValueError, router.build, 'hello', _full=True)
        self.assertRaises(ValueError, router.build, 'hello', _secure=True)

    def test_positions(self):
        template = '/<:\d+>' * 98
        args = tuple(str(i) for i in range(98))
        url = '/' + '/'.join(args)

        route = Route(template)
        self.assertEqual(route.match(Request.blank(url)), (route, args, {}))
        self.assertEqual(route.build(*args), url)

        args = [str(i) for i in range(1000)]
        random.shuffle(args)
        args = tuple(args[:98])
        url = '/' + '/'.join(args)
        self.assertEqual(route.match(Request.blank(url)), (route, args, {}))
        self.assertEqual(route.build(*args), url)

    def test_build_only_without_name(self):
        router = Router()
        self.assertRaises(ValueError, router.add, Route(r'/<foo>', build_only=True), None)

    def test_route_repr(self):
        self.assertEqual(Route(r'/<foo>').__repr__(),
            "Route('/<foo>', name=None, defaults={}, build_only=False)")
        self.assertEqual(Route(r'/<foo>', name='bar', defaults={'baz': 'ding'}, build_only=True).__repr__(),
            "Route('/<foo>', name='bar', defaults={'baz': 'ding'}, build_only=True)")

        self.assertEqual(str(Route(r'/<foo>')),
            "Route('/<foo>', name=None, defaults={}, build_only=False)")
        self.assertEqual(str(Route(r'/<foo>', name='bar', defaults={'baz': 'ding'}, build_only=True)),
            "Route('/<foo>', name='bar', defaults={'baz': 'ding'}, build_only=True)")

    def test_router_repr(self):
        router = Router()
        router.add(Route(r'/hello', name='hello', build_only=True), None)
        router.add(Route(r'/world'), None)

        self.assertEqual(router.__repr__(), "Router([(Route('/world', name=None, defaults={}, build_only=False), None), Route('/hello', name='hello', defaults={}, build_only=True)])")
