# -*- coding: utf-8 -*-
"""
Tests for webapp2 webapp2.RequestHandler
"""
import os
import StringIO
import sys
import unittest
import urllib

from webtest import TestApp

import webapp2


class HomeHandler(webapp2.RequestHandler):
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


class RedirectToHandler(webapp2.RequestHandler):
    def get(self, **kwargs):
        self.redirect_to('route-test', _anchor='my-anchor', year='2010',
            month='07', name='test', foo='bar')


class RedirectAbortHandler(webapp2.RequestHandler):
    def get(self, **kwargs):
        self.redirect('/somewhere', abort=True)


class BrokenHandler(webapp2.RequestHandler):
    def get(self, **kwargs):
        raise ValueError('booo!')


class BrokenButFixedHandler(BrokenHandler):
    def handle_exception(self, exception, debug_mode):
        # Let's fix it.
        self.response.set_status(200)
        self.response.out.write('that was close!')


class Handle404(webapp2.RequestHandler):
    def handle_exception(self, exception, debug_mode):
        self.response.out.write('404 custom handler')
        self.response.set_status(404)


class Handle405(webapp2.RequestHandler):
    def handle_exception(self, exception, debug_mode):
        self.response.out.write('405 custom handler')
        self.response.set_status(405, 'Custom Error Message')
        self.response.headers['Allow'] = 'GET'


class Handle500(webapp2.RequestHandler):
    def handle_exception(self, exception, debug_mode):
        self.response.out.write('500 custom handler')
        self.response.set_status(500)


class PositionalHandler(webapp2.RequestHandler):
    def get(self, month, day, slug=None):
        self.response.out.write('%s:%s:%s' % (month, day, slug))


class HandlerWithError(webapp2.RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('bla bla bla bla bla bla')
        self.error(403)


class InitializeHandler(webapp2.RequestHandler):
    def __init__(self):
        pass

    def get(self):
        self.response.out.write('Request method: %s' % self.request.method)


class WebDavHandler(webapp2.RequestHandler):
    def version_control(self):
        self.response.out.write('Method: VERSION-CONTROL')

    def unlock(self):
        self.response.out.write('Method: UNLOCK')

    def propfind(self):
        self.response.out.write('Method: PROPFIND')


class AuthorizationHandler(webapp2.RequestHandler):
    def get(self):
        self.response.out.write('nothing here')

class HandlerWithEscapedArg(webapp2.RequestHandler):
    def get(self, name):
        self.response.out.write(urllib.unquote_plus(name))

def get_redirect_url(handler, **kwargs):
    return handler.url_for('methods')


app = webapp2.WSGIApplication([
    webapp2.Route('/', HomeHandler, name='home'),
    webapp2.Route('/methods', MethodsHandler, name='methods'),
    webapp2.Route('/broken', BrokenHandler),
    webapp2.Route('/broken-but-fixed', BrokenButFixedHandler),
    webapp2.Route('/<year:\d{4}>/<month:\d\d>/<name>', None, name='route-test'),
    webapp2.Route('/<:\d\d>/<:\d{2}>/<slug>', PositionalHandler, name='positional'),
    webapp2.Route('/redirect-me', webapp2.RedirectHandler, defaults={'url': '/broken'}),
    webapp2.Route('/redirect-me2', webapp2.RedirectHandler, defaults={'url': get_redirect_url}),
    webapp2.Route('/redirect-me3', webapp2.RedirectHandler, defaults={'url': '/broken', 'permanent': False}),
    webapp2.Route('/redirect-me4', webapp2.RedirectHandler, defaults={'url': get_redirect_url, 'permanent': False}),
    webapp2.Route('/redirect-me5', RedirectToHandler),
    webapp2.Route('/redirect-me6', RedirectAbortHandler),
    webapp2.Route('/lazy', 'resources.handlers.LazyHandler'),
    webapp2.Route('/error', HandlerWithError),
    webapp2.Route('/initialize', InitializeHandler),
    webapp2.Route('/webdav', WebDavHandler),
    webapp2.Route('/authorization', AuthorizationHandler),
    webapp2.Route('/escape/<name>', HandlerWithEscapedArg, 'escape'),
], debug=False)

test_app = TestApp(app)

DEFAULT_RESPONSE = """Status: 404 Not Found
content-type: text/html; charset=utf8
Content-Length: 52

404 Not Found

The resource could not be found.

   """

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

    def test_501(self):
        # 501 Not Implemented
        req = webapp2.Request.blank('/methods')
        req.method = 'FOOBAR'
        res = req.get_response(app)
        self.assertEqual(res.status, '501 Not Implemented')

    def test_lazy_handler(self):
        res = test_app.get('/lazy')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'I am a laaazy view.')

    def test_handler_with_error(self):
        res = test_app.get('/error', status=403)
        self.assertEqual(res.status, '403 Forbidden')
        self.assertEqual(res.body, '')

    def test_debug_mode(self):
        app = webapp2.WSGIApplication([
            webapp2.Route('/broken', BrokenHandler),
        ], debug=True)

        test_app = TestApp(app)
        self.assertRaises(ValueError, test_app.get, '/broken')

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
        """Can't test HEAD, OPTIONS and TRACE with webtest?"""
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

        req = webapp2.Request.blank('/methods')
        req.method = 'HEAD'
        res = req.get_response(app)
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, '')

        req = webapp2.Request.blank('/methods')
        req.method = 'OPTIONS'
        res = req.get_response(app)
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'home sweet home - OPTIONS')

        req = webapp2.Request.blank('/methods')
        req.method = 'TRACE'
        res = req.get_response(app)
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, 'home sweet home - TRACE')

    def test_positional(self):
        res = test_app.get('/07/31/test')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, '07:31:test')

        res = test_app.get('/10/18/wooohooo')
        self.assertEqual(res.status, '200 OK')
        self.assertEqual(res.body, '10:18:wooohooo')

    def test_redirect(self):
        res = test_app.get('/redirect-me')
        self.assertEqual(res.status, '301 Moved Permanently')
        self.assertEqual(res.body, '')
        self.assertEqual(res.headers['Location'], 'http://localhost/broken')

    def test_redirect_with_callable(self):
        res = test_app.get('/redirect-me2')
        self.assertEqual(res.status, '301 Moved Permanently')
        self.assertEqual(res.body, '')
        self.assertEqual(res.headers['Location'], 'http://localhost/methods')

    def test_redirect_not_permanent(self):
        res = test_app.get('/redirect-me3')
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.body, '')
        self.assertEqual(res.headers['Location'], 'http://localhost/broken')

    def test_redirect_with_callable_not_permanent(self):
        res = test_app.get('/redirect-me4')
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.body, '')
        self.assertEqual(res.headers['Location'], 'http://localhost/methods')

    def test_redirect_to(self):
        res = test_app.get('/redirect-me5')
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.body, '')
        self.assertEqual(res.headers['Location'], 'http://localhost/2010/07/test?foo=bar#my-anchor')

    def test_redirect_abort(self):
        res = test_app.get('/redirect-me6')
        self.assertEqual(res.status, '302 Found')
        self.assertEqual(res.body, """302 Found

The resource was found at http://localhost/somewhere; you should be redirected automatically.  """)
        self.assertEqual(res.headers['Location'], 'http://localhost/somewhere')

    def test_run(self):
        os.environ['REQUEST_METHOD'] = 'GET'

        app.run()
        self.assertEqual(sys.stdout.getvalue(), DEFAULT_RESPONSE)

    def test_run_bare(self):
        os.environ['REQUEST_METHOD'] = 'GET'
        app.run(bare=True)

        self.assertEqual(sys.stdout.getvalue(), DEFAULT_RESPONSE)

    def test_run_debug(self):
        debug = app.debug
        app.debug = True
        os.environ['REQUEST_METHOD'] = 'GET'

        app.run(bare=True)
        self.assertEqual(sys.stdout.getvalue(), DEFAULT_RESPONSE)

        app.debug = debug

    def test_run_debug2(self):
        import sys
        import webapp2

        path = webapp2._ULTIMATE_SYS_PATH
        webapp2._ULTIMATE_SYS_PATH = []
        debug = app.debug
        app.debug = True
        os.environ['REQUEST_METHOD'] = 'GET'

        app.run(bare=True)
        self.assertEqual(sys.stdout.getvalue(), DEFAULT_RESPONSE)

        app.debug = debug
        webapp2._ULTIMATE_SYS_PATH = sys.path = path

    def test_get_valid_methods(self):
        self.assertEqual(webapp2.get_valid_methods(BrokenHandler).sort(),
            ['GET'].sort())
        self.assertEqual(webapp2.get_valid_methods(HomeHandler).sort(),
            ['GET', 'POST'].sort())
        self.assertEqual(webapp2.get_valid_methods(MethodsHandler).sort(),
            ['GET', 'POST', 'HEAD', 'OPTIONS', 'PUT', 'DELETE', 'TRACE'].sort())

    def test_url_for(self):
        request = webapp2.Request.blank('http://localhost:80/')
        app.request = request
        handler = webapp2.RequestHandler(app, request, None)

        for func in (app.url_for, handler.url_for):
            self.assertEqual(func('home'), '/')
            self.assertEqual(func('home', foo='bar'), '/?foo=bar')
            self.assertEqual(func('home', _anchor='my-anchor', foo='bar'), '/?foo=bar#my-anchor')
            self.assertEqual(func('home', _anchor='my-anchor'), '/#my-anchor')
            self.assertEqual(func('home', _full=True), 'http://localhost:80/')
            self.assertEqual(func('home', _full=True, _anchor='my-anchor'), 'http://localhost:80/#my-anchor')
            self.assertEqual(func('home', _scheme='https'), 'https://localhost:80/')
            self.assertEqual(func('home', _scheme='https', _full=False), 'https://localhost:80/')
            self.assertEqual(func('home', _scheme='https', _anchor='my-anchor'), 'https://localhost:80/#my-anchor')

            self.assertEqual(func('methods'), '/methods')
            self.assertEqual(func('methods', foo='bar'), '/methods?foo=bar')
            self.assertEqual(func('methods', _anchor='my-anchor', foo='bar'), '/methods?foo=bar#my-anchor')
            self.assertEqual(func('methods', _anchor='my-anchor'), '/methods#my-anchor')
            self.assertEqual(func('methods', _full=True), 'http://localhost:80/methods')
            self.assertEqual(func('methods', _full=True, _anchor='my-anchor'), 'http://localhost:80/methods#my-anchor')
            self.assertEqual(func('methods', _scheme='https'), 'https://localhost:80/methods')
            self.assertEqual(func('methods', _scheme='https', _full=False), 'https://localhost:80/methods')
            self.assertEqual(func('methods', _scheme='https', _anchor='my-anchor'), 'https://localhost:80/methods#my-anchor')

            self.assertEqual(func('route-test', year='2010', month='07', name='test'), '/2010/07/test')
            self.assertEqual(func('route-test', year='2010', month='07', name='test', foo='bar'), '/2010/07/test?foo=bar')
            self.assertEqual(func('route-test', _anchor='my-anchor', year='2010', month='07', name='test', foo='bar'), '/2010/07/test?foo=bar#my-anchor')
            self.assertEqual(func('route-test', _anchor='my-anchor', year='2010', month='07', name='test'), '/2010/07/test#my-anchor')
            self.assertEqual(func('route-test', _full=True, year='2010', month='07', name='test'), 'http://localhost:80/2010/07/test')
            self.assertEqual(func('route-test', _full=True, _anchor='my-anchor', year='2010', month='07', name='test'), 'http://localhost:80/2010/07/test#my-anchor')
            self.assertEqual(func('route-test', _scheme='https', year='2010', month='07', name='test'), 'https://localhost:80/2010/07/test')
            self.assertEqual(func('route-test', _scheme='https', _full=False, year='2010', month='07', name='test'), 'https://localhost:80/2010/07/test')
            self.assertEqual(func('route-test', _scheme='https', _anchor='my-anchor', year='2010', month='07', name='test'), 'https://localhost:80/2010/07/test#my-anchor')

        app.request = None

    def test_extra_request_methods(self):
        allowed_methods_backup = webapp2.ALLOWED_METHODS
        webdav_methods = ('VERSION-CONTROL', 'UNLOCK', 'PROPFIND')

        for method in webdav_methods:
            # It is still not possible to use WebDav methods...
            req = webapp2.Request.blank('/webdav')
            req.method = method
            res = req.get_response(app)
            self.assertEqual(res.status, '501 Not Implemented')

        # Let's extend ALLOWED_METHODS with some WebDav methods.
        webapp2.ALLOWED_METHODS = tuple(webapp2.ALLOWED_METHODS) + webdav_methods

        self.assertEqual(sorted(webapp2.get_valid_methods(WebDavHandler)), sorted(list(webdav_methods)))

        # Now we can use WebDav methods...
        for method in webdav_methods:
            req = webapp2.Request.blank('/webdav')
            req.method = method
            res = req.get_response(app)
            self.assertEqual(res.status, '200 OK')
            self.assertEqual(res.body, 'Method: %s' % method)

        # Restore initial values.
        webapp2.ALLOWED_METHODS = allowed_methods_backup
        self.assertEqual(len(webapp2.ALLOWED_METHODS), 7)

    """
    def test_authorization(self):
        response = test_app.get('http://username:password@localhost:8001/authorization')

        self.assertEqual(response.headers, ...)
    """

    def test_escaping(self):
        request = webapp2.Request.blank('http://localhost:80/')
        app.request = request
        handler = webapp2.RequestHandler(app, request, None)

        for func in (app.url_for, handler.url_for):
            res = test_app.get(func('escape', name='with space'))
            self.assertEqual(res.status, '200 OK')
            self.assertEqual(res.body, 'with space')

            res = test_app.get(func('escape', name='with+plus'))
            self.assertEqual(res.status, '200 OK')
            self.assertEqual(res.body, 'with+plus')

    def test_handle_exception_with_error(self):
        class HomeHandler(webapp2.RequestHandler):
            def get(self, **kwargs):
                raise TypeError()

            def handle_exception(self, exception, debug_mode):
                raise ValueError()

        app = webapp2.WSGIApplication([
            webapp2.Route('/', HomeHandler, name='home'),
        ], debug=False)
        app.error_handlers[500] = HomeHandler

        test_app = TestApp(app)
        res = test_app.get('/', status=500)
        self.assertEqual(res.status, '500 Internal Server Error')

    def test_handle_exception_with_error_debug(self):
        class HomeHandler(webapp2.RequestHandler):
            def get(self, **kwargs):
                raise TypeError()

            def handle_exception(self, exception, debug_mode):
                raise ValueError()

        app = webapp2.WSGIApplication([
            webapp2.Route('/', HomeHandler, name='home'),
        ], debug=True)
        app.error_handlers[500] = HomeHandler

        test_app = TestApp(app)
        self.assertRaises(ValueError, test_app.get, '/', status=500)
