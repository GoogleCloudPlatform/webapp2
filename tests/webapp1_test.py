# -*- coding: utf-8 -*-
"""
Tests for webapp2's SimpleRoute
"""
import unittest

from google.appengine.ext import webapp

import webapp2

import test_base


# Old WSGIApplication, new RequestHandler.
class NewStyleHandler(webapp2.RequestHandler):
    def get(self, text):
        self.response.out.write(text)


app = webapp.WSGIApplication([
    (r'/test/(.*)', NewStyleHandler),
])

# New WSGIApplication, old RequestHandler.
class OldStyleHandler(webapp.RequestHandler):
    def get(self, text):
        self.response.out.write(text)

app2 = webapp2.WSGIApplication([
    (r'/test/(.*)', OldStyleHandler),
])


class TestWSGIApplication(test_base.BaseTestCase):
    def test_old_app_new_handler(self):
        req = webapp2.Request.blank('/test/foo')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.body, 'foo')

        req = webapp2.Request.blank('/test/bar')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.body, 'bar')


class TestRequestHandler(test_base.BaseTestCase):
    def test_new_app_old_handler(self):
        req = webapp2.Request.blank('/test/foo')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.body, 'foo')

        req = webapp2.Request.blank('/test/bar')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.body, 'bar')


if __name__ == '__main__':
    test_base.main()
