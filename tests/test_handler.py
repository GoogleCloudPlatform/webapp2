# -*- coding: utf-8 -*-
"""
Tests for webapp2 RequestHandler
"""
import unittest

from webtest import TestApp

from webapp2 import (RedirectHandler, RequestHandler, WSGIApplication,
    get_valid_methods)


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


class UrlForHandler(RequestHandler):
    def get(self, **kwargs):
        assert self.url_for('home') == '/'
        assert self.url_for('home', foo='bar') == '/?foo=bar'
        assert self.url_for('home', _anchor='my-anchor', foo='bar') == '/?foo=bar#my-anchor'
        assert self.url_for('home', _anchor='my-anchor') == '/#my-anchor'
        assert self.url_for('home', _full=True) == 'http://localhost:80/'
        assert self.url_for('home', _full=True, _anchor='my-anchor') == 'http://localhost:80/#my-anchor'
        assert self.url_for('home', _secure=True) == 'https://localhost:80/'
        assert self.url_for('home', _secure=True, _full=False) == 'https://localhost:80/'
        assert self.url_for('home', _secure=True, _anchor='my-anchor') == 'https://localhost:80/#my-anchor'

        assert self.url_for('methods') == '/methods'
        assert self.url_for('methods', foo='bar') == '/methods?foo=bar'
        assert self.url_for('methods', _anchor='my-anchor', foo='bar') == '/methods?foo=bar#my-anchor'
        assert self.url_for('methods', _anchor='my-anchor') == '/methods#my-anchor'
        assert self.url_for('methods', _full=True) == 'http://localhost:80/methods'
        assert self.url_for('methods', _full=True, _anchor='my-anchor') == 'http://localhost:80/methods#my-anchor'
        assert self.url_for('methods', _secure=True) == 'https://localhost:80/methods'
        assert self.url_for('methods', _secure=True, _full=False) == 'https://localhost:80/methods'
        assert self.url_for('methods', _secure=True, _anchor='my-anchor') == 'https://localhost:80/methods#my-anchor'

        assert self.url_for('route-test', year='2010', month='07', name='test') == '/2010/07/test'
        assert self.url_for('route-test', year='2010', month='07', name='test', foo='bar') == '/2010/07/test?foo=bar'
        assert self.url_for('route-test', _anchor='my-anchor', year='2010', month='07', name='test', foo='bar') == '/2010/07/test?foo=bar#my-anchor'
        assert self.url_for('route-test', _anchor='my-anchor', year='2010', month='07', name='test') == '/2010/07/test#my-anchor'
        assert self.url_for('route-test', _full=True, year='2010', month='07', name='test') == 'http://localhost:80/2010/07/test'
        assert self.url_for('route-test', _full=True, _anchor='my-anchor', year='2010', month='07', name='test') == 'http://localhost:80/2010/07/test#my-anchor'
        assert self.url_for('route-test', _secure=True, year='2010', month='07', name='test') == 'https://localhost:80/2010/07/test'
        assert self.url_for('route-test', _secure=True, _full=False, year='2010', month='07', name='test') == 'https://localhost:80/2010/07/test'
        assert self.url_for('route-test', _secure=True, _anchor='my-anchor', year='2010', month='07', name='test') == 'https://localhost:80/2010/07/test#my-anchor'

        self.response.out.write('OK')


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
        self.response.set_status(405, 'Custom Error Message')
        self.response.headers['Allow'] = 'GET'


class Handle500(RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('500 custom handler')
        self.response.set_status(500)


app = WSGIApplication([
    ('/',                 HomeHandler,            'home'),
    ('/methods',          MethodsHandler,         'methods'),
    ('/broken',           BrokenHandler),
    ('/broken-but-fixed', BrokenButFixedHandler),
    ('/url-for',          UrlForHandler),
    ('/{year:\d\d\d\d}/{month:\d\d}/{name}', None, 'route-test'),
], debug=False)

test_app = TestApp(app)


class TestHandler(unittest.TestCase):
    def tearDown(self):
        app.error_handlers = {}

    def test_200(self):
        res = test_app.get('/')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'home sweet home')

    def test_404(self):
        res = test_app.get('/nowhere', status=404)
        self.assertEqual(res.status, '404 Not Found')

    def test_405(self):
        res = test_app.put('/', status=405)
        self.assertEqual(res.status, '405 Method Not Allowed')
        self.assertEqual(res.headers.get('Allow'), 'GET, POST')

    def test_500(self):
        res = test_app.get('/broken', status=500)
        self.assertEqual(res.status, '500 Internal Server Error')

    def test_500_but_fixed(self):
        res = test_app.get('/broken-but-fixed')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'that was close!')

    def test_custom_error_handlers(self):
        app.error_handlers = {
            404: Handle404,
            405: Handle405,
            500: Handle500,
        }

        res = test_app.get('/nowhere', status=404)
        self.assertEqual(res.status, '404 Not Found')
        self.assertEqual(res.body, '404 custom handler')

        res = test_app.put('/', status=405)
        self.assertEqual(res.status, '405 Custom Error Message')
        self.assertEqual(res.body, '405 custom handler')
        self.assertEqual(res.headers.get('Allow'), 'GET')

        res = test_app.get('/broken', status=500)
        self.assertEqual(res.status, '500 Internal Server Error')
        self.assertEqual(res.body, '500 custom handler')

    def test_methods(self):
        """Can't test HEAD, OPTIONS and TRACE with webtest."""
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

    def test_url_for(self):
        res = test_app.get('/url-for')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'OK')


class TestHandlerHelpers(unittest.TestCase):
    def test_get_valid_methods(self):
        self.assertEqual(get_valid_methods(BrokenHandler).sort(),
            ['GET'].sort())
        self.assertEqual(get_valid_methods(HomeHandler).sort(),
            ['GET', 'POST'].sort())
        self.assertEqual(get_valid_methods(MethodsHandler).sort(),
            ['GET', 'POST', 'HEAD', 'OPTIONS', 'PUT', 'DELETE', 'TRACE'].sort())
