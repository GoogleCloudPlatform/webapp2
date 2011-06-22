# -*- coding: utf-8 -*-
import webapp2

import test_base


class TestReturnResponse(test_base.BaseTestCase):
    def test_function_that_returns_response(self):
        def myfunction(request, response):
            return webapp2.Response('Hello, custom response world!')

        app = webapp2.WSGIApplication([
            ('/', myfunction),
        ], debug=True)

        req = webapp2.Request.blank('/')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 200)
        self.assertEqual(rsp.body, 'Hello, custom response world!')

    def test_function_that_returns_string(self):
        def myfunction(request, response):
            return 'Hello, custom response world!'

        app = webapp2.WSGIApplication([
            ('/', myfunction),
        ], debug=True)

        def custom_dispatcher(router, request, response):
            response_str = router.default_dispatcher(request, response)
            return request.app.response_class(response_str)

        app.router.set_dispatcher(custom_dispatcher)

        req = webapp2.Request.blank('/')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 200)
        self.assertEqual(rsp.body, 'Hello, custom response world!')

    def test_function_that_returns_tuple(self):
        def myfunction(request, response):
            return 'Hello, custom response world!', 404

        app = webapp2.WSGIApplication([
            ('/', myfunction),
        ], debug=True)

        def custom_dispatcher(router, request, response):
            response_tuple = router.default_dispatcher(request, response)
            return request.app.response_class(*response_tuple)

        app.router.set_dispatcher(custom_dispatcher)

        req = webapp2.Request.blank('/')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 404)
        self.assertEqual(rsp.body, 'Hello, custom response world!')

    def test_handle_exception_that_returns_response(self):
        class HomeHandler(webapp2.RequestHandler):
            def get(self, **kwargs):
                raise TypeError()

        app = webapp2.WSGIApplication([
            webapp2.Route('/', HomeHandler, name='home'),
        ], debug=True)
        app.error_handlers[500] = 'resources.handlers.handle_exception'

        req = webapp2.Request.blank('/')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 200)
        self.assertEqual(rsp.body, 'Hello, custom response world!')

    def test_return_is_not_wsgi_app(self):
        class HomeHandler(webapp2.RequestHandler):
            def get(self, **kwargs):
                return ''

        app = webapp2.WSGIApplication([
            webapp2.Route('/', HomeHandler, name='home'),
        ], debug=False)

        req = webapp2.Request.blank('/')
        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 500)


if __name__ == '__main__':
    test_base.main()
