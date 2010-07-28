import unittest

from webapp2 import Route, Router


class TestRoute(unittest.TestCase):
    def test_no_variable(self):
        route = Route('/hello', 'hello_handler')
        matched_route, kwargs = route.match('/hello')
        self.assertEqual(matched_route, route)
        self.assertEqual(kwargs, {})
        self.assertEqual(matched_route.handler, 'hello_handler')
        self.assertEqual(route.build(), '/hello')

        route = Route('/hello/world/', 'hello_world_handler')
        matched_route, kwargs = route.match('/hello/world/')
        self.assertEqual(matched_route, route)
        self.assertEqual(kwargs, {})
        self.assertEqual(matched_route.handler, 'hello_world_handler')
        self.assertEqual(route.build(), '/hello/world/')

    def test_simple_variable(self):
        route = Route('/{foo}', 'my_handler')
        self.assertEqual(route.match('/bar'), (route, {'foo': 'bar'}))
        self.assertEqual(route.build(foo='baz'), '/baz')

    def test_expr_variable(self):
        route = Route('/{year:\d\d\d\d}', 'my_handler')
        self.assertEqual(route.match('/bar'), None)
        self.assertEqual(route.match('/2010'), (route, {'year': '2010'}))
        self.assertEqual(route.match('/1900'), (route, {'year': '1900'}))
        self.assertEqual(route.build(year='2010'), '/2010')

    def test_expr_variable2(self):
        route = Route('/{year:\d\d\d\d}/foo/', 'my_handler')
        self.assertEqual(route.build(year='2010'), '/2010/foo/')


if __name__ == '__main__':
    unittest.main()
