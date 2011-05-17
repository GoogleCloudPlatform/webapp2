# -*- coding: utf-8 -*-
import webapp2

import test_base

from protorpc import messages
from protorpc import remote

from webapp2_extras import protorpc as service_handlers

# Hello service ---------------------------------------------------------------

class HelloRequest(messages.Message):
    my_name = messages.StringField(1, required=True)

class HelloResponse(messages.Message):
    hello = messages.StringField(1, required=True)

class HelloService(remote.Service):
    @remote.method(HelloRequest, HelloResponse)
    def hello(self, request):
        return HelloResponse(hello='Hello, %s!' %
                             request.my_name)

    @remote.method(HelloRequest, HelloResponse)
    def hello_error(self, request):
        raise ValueError()

class AhoyService(remote.Service):
    @remote.method(HelloRequest, HelloResponse)
    def ahoy(self, request):
        return HelloResponse(hello='Ahoy, %s!' %
                             request.my_name)

class HolaService(remote.Service):
    @remote.method(HelloRequest, HelloResponse)
    def hola(self, request):
        return HelloResponse(hello='Hola, %s!' %
                             request.my_name)

service_mappings = service_handlers.service_mapping([
    ('/hello', HelloService),
    AhoyService,
])
app = webapp2.WSGIApplication(service_mappings, debug=True)

service_mappings2 = service_handlers.service_mapping({
    '/hola': HolaService,
})
app2 = webapp2.WSGIApplication(service_mappings2, debug=True)

# Tests -----------------------------------------------------------------------

class TestProtoRPC(test_base.BaseTestCase):

    def test_example(self):
        req = webapp2.Request.blank('/hello.hello')
        req.method = 'POST'
        req.headers['Content-Type'] = 'application/json'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(resp.body, '{"hello": "Hello, bob!"}')

    def test_ahoy(self):
        req = webapp2.Request.blank('/protorpc_test/AhoyService.ahoy')
        req.method = 'POST'
        req.headers['Content-Type'] = 'application/json'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(resp.body, '{"hello": "Ahoy, bob!"}')

    def test_hola(self):
        req = webapp2.Request.blank('/hola.hola')
        req.method = 'POST'
        req.headers['Content-Type'] = 'application/json'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app2)
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(resp.body, '{"hello": "Hola, bob!"}')

    def test_unrecognized_rpc_format(self):
        # No content type
        req = webapp2.Request.blank('/hello.hello')
        req.method = 'POST'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '400 Bad Request')

        # Invalid content type
        req = webapp2.Request.blank('/hello.hello')
        req.method = 'POST'
        req.headers['Content-Type'] = 'text/xml'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '400 Bad Request')

        # Bad request method
        req = webapp2.Request.blank('/hello.hello')
        req.method = 'PUT'
        req.headers['Content-Type'] = 'application/json'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '400 Bad Request')

    def test_invalid_method(self):
        # Bad request method
        req = webapp2.Request.blank('/hello.ahoy')
        req.method = 'POST'
        req.headers['Content-Type'] = 'application/json'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '400 Bad Request')

    def test_invalid_json(self):
        # Bad request method
        req = webapp2.Request.blank('/hello.hello')
        req.method = 'POST'
        req.headers['Content-Type'] = 'application/json'
        req.body = '"my_name": "bob"'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '400 Bad Request')

    def test_response_error(self):
        # Bad request method
        req = webapp2.Request.blank('/hello.hello_error')
        req.method = 'POST'
        req.headers['Content-Type'] = 'application/json'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '500 Internal Server Error')

    def test_invalid_paths(self):
        # Not starting with slash.
        self.assertRaises(ValueError, service_handlers.service_mapping, [
            ('hello', HelloService),
        ])
        # Trailing slash.
        self.assertRaises(ValueError, service_handlers.service_mapping, [
            ('/hello/', HelloService),
        ])
        # Double paths.
        self.assertRaises(service_handlers.service_handlers.ServiceConfigurationError,
            service_handlers.service_mapping, [
                ('/hello', HelloService),
                ('/hello', HelloService),
            ]
        )

    def test_lazy_services(self):
        service_mappings = service_handlers.service_mapping([
            ('/bonjour', 'resources.protorpc_services.BonjourService'),
            'resources.protorpc_services.CiaoService',
        ])
        app = webapp2.WSGIApplication(service_mappings, debug=True)

        # Bonjour
        req = webapp2.Request.blank('/bonjour.bonjour')
        req.method = 'POST'
        req.headers['Content-Type'] = 'application/json'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(resp.body, '{"hello": "Bonjour, bob!"}')

        # Ciao
        req = webapp2.Request.blank('/resources/protorpc_services/CiaoService.ciao')
        req.method = 'POST'
        req.headers['Content-Type'] = 'application/json'
        req.body = '{"my_name": "bob"}'

        resp = req.get_response(app)
        self.assertEqual(resp.status, '200 OK')
        self.assertEqual(resp.body, '{"hello": "Ciao, bob!"}')


if __name__ == '__main__':
    test_base.main()
