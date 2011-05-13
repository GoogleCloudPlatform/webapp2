# -*- coding: utf-8 -*-
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

class OldStyleHandlerWithError(webapp.RequestHandler):
    def get(self, text):
        raise ValueError()

    def handle_exception(self, e, debug):
        self.response.set_status(500)
        self.response.out.write('ValueError!')

app2 = webapp2.WSGIApplication([
    (r'/test/error', OldStyleHandlerWithError),
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

        self.assertTrue(issubclass(OldStyleHandler, webapp.RequestHandler))


class TestRequestHandler(test_base.BaseTestCase):
    def test_new_app_old_handler(self):
        req = webapp2.Request.blank('/test/foo')
        rsp = req.get_response(app2)
        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.body, 'foo')

        req = webapp2.Request.blank('/test/bar')
        rsp = req.get_response(app2)
        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.body, 'bar')

    def test_new_app_old_handler_405(self):
        req = webapp2.Request.blank('/test/foo')
        req.method = 'POST'
        rsp = req.get_response(app2)
        self.assertEqual(rsp.status, '405 Method Not Allowed')
        self.assertEqual(rsp.headers.get('Allow'), None)

    def test_new_app_old_handler_501(self):
        req = webapp2.Request.blank('/test/foo')
        req.method = 'WHATMETHODISTHIS'
        rsp = req.get_response(app2)
        self.assertEqual(rsp.status, '501 Not Implemented')

    def test_new_app_old_handler_with_error(self):
        req = webapp2.Request.blank('/test/error')
        rsp = req.get_response(app2)
        self.assertEqual(rsp.status, '500 Internal Server Error')
        self.assertEqual(rsp.body, 'ValueError!')


if __name__ == '__main__':
    test_base.main()
