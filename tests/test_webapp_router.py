# -*- coding: utf-8 -*-
"""
Tests for webapp2 webapp router
"""
import unittest

from webapp2 import Request, Router, SimpleRoute


class TestSimpleRoute(unittest.TestCase):
    def test_no_variable(self):
        router = Router([(r'/', 'my_handler')])

        handler, matched_route, args, kwargs = router.match(Request.blank('/'))
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})

    def test_simple_variables(self):
        router = Router([(r'/(\d{4})/(\d{2})', 'my_handler')])

        handler, matched_route, args, kwargs = router.match(Request.blank('/2007/10'))
        self.assertEqual(args, ('2007', '10'))
        self.assertEqual(kwargs, {})

    def test_build(self):
        route = SimpleRoute('/')
        self.assertRaises(NotImplementedError, route.build)
