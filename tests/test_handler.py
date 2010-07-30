# -*- coding: utf-8 -*-
"""
Tests for webapp2 RequestHandler
"""
import unittest

from webtest import TestApp

from webapp2 import RedirectHandler, RequestHandler, WSGIApplication


class HomeHandler(RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('home sweet home')

app = WSGIApplication([
    ('/', HomeHandler, 'home'),
], debug=False)


class TestHandler(unittest.TestCase):
    def test_200(self):
        test_app = TestApp(app)
        res = test_app.get('/')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'home sweet home')

    def test_404(self):
        test_app = TestApp(app)
        res = test_app.get('/nowhere', status=404)
        self.assertEqual(res.status, '404 Not Found')

    def test_405(self):
        test_app = TestApp(app)
        res = test_app.put('/', status=405)
        self.assertEqual(res.status, '405 Method Not Allowed')
