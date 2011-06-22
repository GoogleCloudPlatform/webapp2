# -*- coding: utf-8 -*-
import webapp2

import test_base


class TestSimpleRoute(test_base.BaseTestCase):
    def test_no_variable(self):
        router = webapp2.Router([(r'/', 'my_handler')])

        matched_route, args, kwargs = router.match(webapp2.Request.blank('/'))
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})

    def test_simple_variables(self):
        router = webapp2.Router([(r'/(\d{4})/(\d{2})', 'my_handler')])

        matched_route, args, kwargs = router.match(webapp2.Request.blank('/2007/10'))
        self.assertEqual(args, ('2007', '10'))
        self.assertEqual(kwargs, {})

    def test_build(self):
        route = webapp2.SimpleRoute('/', None)
        self.assertRaises(NotImplementedError, route.build, None, None, None)

    def test_route_repr(self):
        self.assertEqual(webapp2.SimpleRoute(r'/<foo>', None).__repr__(), "<SimpleRoute('/<foo>', None)>")
        self.assertEqual(str(webapp2.SimpleRoute(r'/<foo>', None)), "<SimpleRoute('/<foo>', None)>")


if __name__ == '__main__':
    test_base.main()
