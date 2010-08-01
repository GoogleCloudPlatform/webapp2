# -*- coding: utf-8 -*-
"""
Tests for webapp2 webapp router
"""
import unittest

from webapp2 import Request, Router, WebappRoute


class TestWebappRoute(unittest.TestCase):
    def test_no_variable(self):
        router = Router([(r'/', 'my_handler')])

        matched_route, args, kwargs = router.match(Request.blank('/'))
        self.assertEqual(args, ())
        self.assertEqual(kwargs, {})
        self.assertEqual(matched_route.handler, 'my_handler')

    def test_simple_variables(self):
        router = Router([(r'/(\d{4})/(\d{2})', 'my_handler')])

        matched_route, args, kwargs = router.match(Request.blank('/2007/10'))
        self.assertEqual(args, ('2007', '10'))
        self.assertEqual(kwargs, {})
        self.assertEqual(matched_route.handler, 'my_handler')
