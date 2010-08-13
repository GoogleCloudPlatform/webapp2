# -*- coding: utf-8 -*-
"""
Tests for webapp2's SimpleRoute
"""
import unittest

from google.appengine.ext import webapp

import webapp2

from webtest import TestApp


# Old WSGIApplication, new RequestHandler.
class NewStyleHandler(webapp2.RequestHandler):
    def get(self, text):
        self.response.out.write(text)


app = webapp.WSGIApplication([
    (r'/test/(.*)', NewStyleHandler),
])

test_app = TestApp(app)

# New WSGIApplication, old RequestHandler.
class OldStyleHandler(webapp.RequestHandler):
    def get(self, text):
        self.response.out.write(text)

app2 = webapp2.WSGIApplication([
    (r'/test/(.*)', OldStyleHandler),
])

test_app2 = TestApp(app2)


class TestWSGIApplication(unittest.TestCase):
    def test_old_app_new_handler(self):
        res = test_app.get('/test/foo')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'foo')

        res = test_app.get('/test/bar')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'bar')


class TestRequestHandler(unittest.TestCase):
    def test_new_app_old_handler(self):
        res = test_app2.get('/test/foo')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'foo')

        res = test_app2.get('/test/bar')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'bar')
