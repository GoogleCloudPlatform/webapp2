# -*- coding: utf-8 -*-
"""
Tests for webapp2's SimpleRoute
"""
import unittest

from webapp2 import Request, Router, SimpleRoute


class TestSimpleRoute(unittest.TestCase):
    def test_no_variable(self):
        router = Router(None, [(r'/', 'my_handler')])

        matched_route, args, kwargs = router.match(Request.blank('/'))
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})

    def test_simple_variables(self):
        router = Router(None, [(r'/(\d{4})/(\d{2})', 'my_handler')])

        matched_route, args, kwargs = router.match(Request.blank('/2007/10'))
        self.assertEqual(args, ('2007', '10'))
        self.assertEqual(kwargs, {})

    def test_build(self):
        route = SimpleRoute('/', None)
        self.assertRaises(NotImplementedError, route.build, None, None, None)

    def test_route_repr(self):
        self.assertEqual(SimpleRoute(r'/<foo>', None).__repr__(), "<SimpleRoute('/<foo>', None)>")
        self.assertEqual(str(SimpleRoute(r'/<foo>', None)), "<SimpleRoute('/<foo>', None)>")
