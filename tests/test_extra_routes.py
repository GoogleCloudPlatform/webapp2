# -*- coding: utf-8 -*-
"""
Tests for extra routes not included in webapp2 (see extras/routes.py)
"""
import random
import unittest

from webapp2 import Request, Route, Router

from extras.routes import PrefixRoute, NamePrefixRoute, HandlerPrefixRoute


class TestPrefixRoute(unittest.TestCase):
    def test_simple(self):
        router = Router([
            PrefixRoute('/a', [
                Route('/', 'a', 'name-a'),
                Route('/b', 'a/b', 'name-a/b'),
                Route('/c', 'a/c', 'name-a/c'),
                PrefixRoute('/d', [
                    Route('/', 'a/d', 'name-a/d'),
                    Route('/b', 'a/d/b', 'name-a/d/b'),
                    Route('/c', 'a/d/c', 'name-a/d/c'),
                ]),
            ])
        ])

        path = '/a/'
        match = ('a', (), {})
        self.assertEqual(router.match(Request.blank(path)), match)
        self.assertEqual(router.build('name-' + match[0], Request.blank('/'), match[1], match[2]), path)

        path = '/a/b'
        match = ('a/b', (), {})
        self.assertEqual(router.match(Request.blank(path)), match)
        self.assertEqual(router.build('name-' + match[0], Request.blank('/'), match[1], match[2]), path)

        path = '/a/c'
        match = ('a/c', (), {})
        self.assertEqual(router.match(Request.blank(path)), match)
        self.assertEqual(router.build('name-' + match[0], Request.blank('/'), match[1], match[2]), path)

        path = '/a/d/'
        match = ('a/d', (), {})
        self.assertEqual(router.match(Request.blank(path)), match)
        self.assertEqual(router.build('name-' + match[0], Request.blank('/'), match[1], match[2]), path)

        path = '/a/d/b'
        match = ('a/d/b', (), {})
        self.assertEqual(router.match(Request.blank(path)), match)
        self.assertEqual(router.build('name-' + match[0], Request.blank('/'), match[1], match[2]), path)

        path = '/a/d/c'
        match = ('a/d/c', (), {})
        self.assertEqual(router.match(Request.blank(path)), match)
        self.assertEqual(router.build('name-' + match[0], Request.blank('/'), match[1], match[2]), path)

    def test_with_variables_name_and_handler(self):
        router = Router([
                PrefixRoute('/user/<username:\w+>', [
                    HandlerPrefixRoute('apps.users.', [
                        NamePrefixRoute('user-', [
                            Route('/', 'UserOverviewHandler', 'overview'),
                            Route('/profile', 'UserProfileHandler', 'profile'),
                            Route('/projects', 'UserProjectsHandler', 'projects'),
                        ]),
                    ]),
            ])
        ])

        path = '/user/calvin/'
        match = ('apps.users.UserOverviewHandler', (), {'username': 'calvin'})
        self.assertEqual(router.match(Request.blank(path)), match)
        self.assertEqual(router.build('user-overview', Request.blank('/'), match[1], match[2]), path)

        path = '/user/calvin/profile'
        match = ('apps.users.UserProfileHandler', (), {'username': 'calvin'})
        self.assertEqual(router.match(Request.blank(path)), match)
        self.assertEqual(router.build('user-profile', Request.blank('/'), match[1], match[2]), path)

        path = '/user/calvin/projects'
        match = ('apps.users.UserProjectsHandler', (), {'username': 'calvin'})
        self.assertEqual(router.match(Request.blank(path)), match)
        self.assertEqual(router.build('user-projects', Request.blank('/'), match[1], match[2]), path)

