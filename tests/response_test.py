# -*- coding: utf-8 -*-
import webapp2

import test_base


class NoStringOrUnicodeConversion(object):
    pass


class StringConversion(object):
    def __str__(self):
        return 'foo'.encode('utf-8')


class UnicodeConversion(object):
    def __unicode__(self):
        return 'bar'.decode('utf-8')


class TestResponse(test_base.BaseTestCase):
    def test_write(self):
        var_1 = NoStringOrUnicodeConversion()
        var_2 = StringConversion()
        var_3 = UnicodeConversion()

        rsp = webapp2.Response()
        rsp.write(var_1)
        rsp.write(var_2)
        rsp.write(var_3)
        self.assertEqual(rsp.body, '%rfoobar' % var_1)

        rsp = webapp2.Response()
        rsp.write(var_1)
        rsp.write(var_3)
        rsp.write(var_2)
        self.assertEqual(rsp.body, '%rbarfoo' % var_1)

        rsp = webapp2.Response()
        rsp.write(var_2)
        rsp.write(var_1)
        rsp.write(var_3)
        self.assertEqual(rsp.body, 'foo%rbar' % var_1)

        rsp = webapp2.Response()
        rsp.write(var_2)
        rsp.write(var_3)
        rsp.write(var_1)
        self.assertEqual(rsp.body, 'foobar%r' % var_1)

        rsp = webapp2.Response()
        rsp.write(var_3)
        rsp.write(var_1)
        rsp.write(var_2)
        self.assertEqual(rsp.body, 'bar%rfoo' % var_1)

        rsp = webapp2.Response()
        rsp.write(var_3)
        rsp.write(var_2)
        rsp.write(var_1)
        self.assertEqual(rsp.body, 'barfoo%r' % var_1)

    def test_write2(self):
        rsp = webapp2.Response()
        rsp.charset = None
        rsp.write(u'foo')

        self.assertEqual(rsp.body, u'foo')
        self.assertEqual(rsp.charset, 'utf-8')

    def test_status(self):
        rsp = webapp2.Response()

        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.status_int, 200)
        self.assertEqual(rsp.status_message, 'OK')

        rsp.status = u'200 OK'
        self.assertEqual(rsp.status, '200 OK')
        self.assertEqual(rsp.status_int, 200)
        self.assertEqual(rsp.status_message, 'OK')

        rsp.status_message = 'Weee'
        self.assertEqual(rsp.status, '200 Weee')
        self.assertEqual(rsp.status_int, 200)
        self.assertEqual(rsp.status_message, 'Weee')

        rsp.status = 404
        self.assertEqual(rsp.status, '404 Not Found')
        self.assertEqual(rsp.status_int, 404)
        self.assertEqual(rsp.status_message, 'Not Found')

        rsp.status = '403 Wooo'
        self.assertEqual(rsp.status, '403 Wooo')
        self.assertEqual(rsp.status_int, 403)
        self.assertEqual(rsp.status_message, 'Wooo')

        rsp.status_int = 500
        self.assertEqual(rsp.status, '500 Internal Server Error')
        self.assertEqual(rsp.status_int, 500)
        self.assertEqual(rsp.status_message, 'Internal Server Error')

        self.assertRaises(TypeError, rsp._set_status, ())

    def test_has_error(self):
        rsp = webapp2.Response()
        self.assertFalse(rsp.has_error())
        rsp.status = 400
        self.assertTrue(rsp.has_error())
        rsp.status = 404
        self.assertTrue(rsp.has_error())
        rsp.status = 500
        self.assertTrue(rsp.has_error())
        rsp.status = 200
        self.assertFalse(rsp.has_error())
        rsp.status = 302
        self.assertFalse(rsp.has_error())

    def test_wsgi_write(self):
        res = []

        def write(status, headers, body):
            return res.extend([status, headers, body])

        def start_response(status, headers):
            return lambda body: write(status, headers, body)

        rsp = webapp2.Response(body='Page not found!', status=404)
        rsp.wsgi_write(start_response)
        self.assertEqual(res, [
            '404 Not Found',
            [
                ('Content-Type', 'text/html; charset=utf-8'),
                ('Cache-Control', 'no-cache'),
                ('Expires', 'Fri, 01 Jan 1990 00:00:00 GMT'),
                ('Content-Length', '15')
            ],
            'Page not found!'
        ])


if __name__ == '__main__':
    test_base.main()
