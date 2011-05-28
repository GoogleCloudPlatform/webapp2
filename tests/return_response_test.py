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
        self.assertEqual(rsp.status, '200 OK')
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
        self.assertEqual(rsp.status, '200 OK')
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
        self.assertEqual(rsp.status, '404 Not Found')
        self.assertEqual(rsp.body, 'Hello, custom response world!')


if __name__ == '__main__':
    test_base.main()
