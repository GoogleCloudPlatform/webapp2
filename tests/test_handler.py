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

    def post(self, **kwargs):
        self.response.out.write('home sweet home - POST')


class MethodsHandler(HomeHandler):
    def put(self, **kwargs):
        self.response.out.write('home sweet home - PUT')

    def delete(self, **kwargs):
        self.response.out.write('home sweet home - DELETE')

    def head(self, **kwargs):
        self.response.out.write('home sweet home - HEAD')

    def trace(self, **kwargs):
        self.response.out.write('home sweet home - TRACE')

    def options(self, **kwargs):
        self.response.out.write('home sweet home - OPTIONS')


class BrokenHandler(RequestHandler):
    def get(self, **kwargs):
        raise ValueError('booo!')


class BrokenButFixedHandler(BrokenHandler):
    def handle_exception(self, exception, debug_mode):
        # Let's fix it.
        self.response.set_status(200)
        self.response.out.write('that was close!')


class Handle404(RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('404 custom handler')
        self.response.set_status(404)


class Handle405(RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('405 custom handler')
        self.response.set_status(405)
        self.response.headers['Allow'] = 'GET'


class Handle500(RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('500 custom handler')
        self.response.set_status(500)


app = WSGIApplication([
    ('/', HomeHandler),
    ('/methods', MethodsHandler),
    ('/broken', BrokenHandler),
    ('/broken-but-fixed', BrokenButFixedHandler),
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
        self.assertEqual(res.headers.get('Allow'), 'GET, POST')

    def test_500(self):
        test_app = TestApp(app)
        res = test_app.get('/broken', status=500)
        self.assertEqual(res.status, '500 Internal Server Error')

    def test_500_but_fixed(self):
        test_app = TestApp(app)
        res = test_app.get('/broken-but-fixed')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'that was close!')

    def test_custom_error_handlers(self):
        app = WSGIApplication([
            ('/', HomeHandler),
            ('/broken', BrokenHandler),
        ], debug=False)

        app.error_handlers = {
            404: Handle404,
            405: Handle405,
            500: Handle500,
        }

        test_app = TestApp(app)

        res = test_app.get('/nowhere', status=404)
        self.assertEqual(res.status, '404 Not Found')
        self.assertEqual(res.body, '404 custom handler')

        res = test_app.put('/', status=405)
        self.assertEqual(res.status, '405 Method Not Allowed')
        self.assertEqual(res.body, '405 custom handler')
        self.assertEqual(res.headers.get('Allow'), 'GET')

        res = test_app.get('/broken', status=500)
        self.assertEqual(res.status, '500 Internal Server Error')
        self.assertEqual(res.body, '500 custom handler')

    def test_methods(self):
        """Can't test HEAD, OPTIONS and TRACE with webtest."""
        test_app = TestApp(app)

        res = test_app.get('/methods')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'home sweet home')

        res = test_app.post('/methods')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'home sweet home - POST')

        res = test_app.put('/methods')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'home sweet home - PUT')

        res = test_app.delete('/methods')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'home sweet home - DELETE')
