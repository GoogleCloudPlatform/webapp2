import os
import sys
import unittest

path = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, path)

from webapp2 import Request, Route, Router


class TestRoute(unittest.TestCase):
    def test_no_variable(self):
        route = Route('/hello', 'hello_handler')
        matched_route, kwargs = route.match(Request.blank('/hello'))
        self.assertEqual(matched_route, route)
        self.assertEqual(kwargs, {})
        self.assertEqual(matched_route.handler, 'hello_handler')
        self.assertEqual(route.build(), '/hello')

        route = Route('/hello/world/', 'hello_world_handler')
        matched_route, kwargs = route.match(Request.blank('/hello/world/'))
        self.assertEqual(matched_route, route)
        self.assertEqual(kwargs, {})
        self.assertEqual(matched_route.handler, 'hello_world_handler')
        self.assertEqual(route.build(), '/hello/world/')

    def test_simple_variable(self):
        route = Route('/{foo}', 'my_handler')
        self.assertEqual(route.match(Request.blank('/bar')),
            (route, {'foo': 'bar'}))
        self.assertEqual(route.build(foo='baz'), '/baz')

    def test_expr_variable(self):
        route = Route('/{year:\d\d\d\d}', 'my_handler')
        self.assertEqual(route.match(Request.blank('/bar')), None)
        self.assertEqual(route.match(Request.blank('/2010')), (route, {'year': '2010'}))
        self.assertEqual(route.match(Request.blank('/1900')), (route, {'year': '1900'}))
        self.assertEqual(route.build(year='2010'), '/2010')

    def test_expr_variable2(self):
        route = Route('/{year:\d\d\d\d}/foo/', 'my_handler')
        self.assertEqual(route.build(year='2010'), '/2010/foo/')

    def test_build_invalid_keyword(self):
        route = Route('/{year:\d\d\d\d}', 'my_handler')
        self.assertRaises(ValueError, route.build, year='20100')

    def test_build_invalid_keyword2(self):
        route = Route('/{year:\d\d\d\d}', 'my_handler')
        self.assertRaises(ValueError, route.build, year='201a')

    def test_build_missing_keyword(self):
        route = Route('/{year:\d\d\d\d}', 'my_handler')
        self.assertRaises(ValueError, route.build)

    def test_build_missing_keyword2(self):
        route = Route('/{year:\d\d\d\d}/{month:\d\d}', 'my_handler')
        self.assertRaises(ValueError, route.build, year='2010')

    def test_build_default_keyword(self):
        route = Route('/{year:\d\d\d\d}/{month:\d\d}', 'my_handler', month=10)
        self.assertEqual(route.build(year='2010'), '/2010/10')

        route = Route('/{year:\d\d\d\d}/{month:\d\d}', 'my_handler', year=1900)
        self.assertEqual(route.build(month='07'), '/1900/07')

    def test_build_extra_keyword(self):
        route = Route('/{year:\d\d\d\d}', 'my_handler')
        self.assertEqual(route.build(year='2010', foo='bar'), '/2010?foo=bar')
        self.assertEqual(route.build(year='2010', foo='bar', baz='ding'), '/2010?foo=bar&baz=ding')

    def test_build_int_keyword(self):
        route = Route('/{year:\d\d\d\d}', 'my_handler')
        self.assertEqual(route.build(year=2010), '/2010')


if __name__ == '__main__':
    unittest.main()
