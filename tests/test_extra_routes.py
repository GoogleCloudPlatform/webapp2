# -*- coding: utf-8 -*-
"""
Tests for extra routes not included in webapp2 (see extras/routes.py)
"""
import random
import unittest

from webapp2 import Request, Route, Router

from extras.routes import PrefixRoute


class TestPrefixRoute(unittest.TestCase):
    def test_simple(self):
        router = Router([
            PrefixRoute('/a', [
                Route('/', 'a'),
                Route('/b', 'a/b'),
                Route('/c', 'a/c'),
                PrefixRoute('/d', [
                    Route('/', 'a/d'),
                    Route('/b', 'a/d/b'),
                    Route('/c', 'a/d/c'),
                ]),
            ])
        ])

        match = router.match(Request.blank('/a/'))
        self.assertEqual(match, ('a', (), {}))

        match = router.match(Request.blank('/a/b'))
        self.assertEqual(match, ('a/b', (), {}))

        match = router.match(Request.blank('/a/c'))
        self.assertEqual(match, ('a/c', (), {}))

        match = router.match(Request.blank('/a/d/'))
        self.assertEqual(match, ('a/d', (), {}))

        match = router.match(Request.blank('/a/d/b'))
        self.assertEqual(match, ('a/d/b', (), {}))

        match = router.match(Request.blank('/a/d/c'))
        self.assertEqual(match, ('a/d/c', (), {}))

    def test_with_variables(self):
        router = Router([
            PrefixRoute('/user/<username:\w+>', [
                Route('/', 'user-overview'),
                Route('/profile', 'user-profile'),
                Route('/projects', 'user-projects'),
            ])
        ])

        match = router.match(Request.blank('/user/calvin/'))
        self.assertEqual(match, ('user-overview', (), {'username': 'calvin'}))

        match = router.match(Request.blank('/user/calvin/profile'))
        self.assertEqual(match, ('user-profile', (), {'username': 'calvin'}))

        match = router.match(Request.blank('/user/calvin/projects'))
        self.assertEqual(match, ('user-projects', (), {'username': 'calvin'}))
