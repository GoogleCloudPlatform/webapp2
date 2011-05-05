# -*- coding: utf-8 -*-
"""
Tests for webapp2 RequestHandler
"""
import unittest

import webob
import webob.exc

from webapp2 import (RedirectHandler, RequestHandler, Response,
    WSGIApplication, abort, import_string, to_unicode, to_utf8)

import test_base


class TestMiscellaneous(test_base.BaseTestCase):
    def test_abort(self):
        self.assertRaises(webob.exc.HTTPOk, abort, 200)
        self.assertRaises(webob.exc.HTTPCreated, abort, 201)
        self.assertRaises(webob.exc.HTTPAccepted, abort, 202)
        self.assertRaises(webob.exc.HTTPNonAuthoritativeInformation, abort, 203)
        self.assertRaises(webob.exc.HTTPNoContent, abort, 204)
        self.assertRaises(webob.exc.HTTPResetContent, abort, 205)
        self.assertRaises(webob.exc.HTTPPartialContent, abort, 206)
        self.assertRaises(webob.exc.HTTPMultipleChoices, abort, 300)
        self.assertRaises(webob.exc.HTTPMovedPermanently, abort, 301)
        self.assertRaises(webob.exc.HTTPFound, abort, 302)
        self.assertRaises(webob.exc.HTTPSeeOther, abort, 303)
        self.assertRaises(webob.exc.HTTPNotModified, abort, 304)
        self.assertRaises(webob.exc.HTTPUseProxy, abort, 305)
        self.assertRaises(webob.exc.HTTPTemporaryRedirect, abort, 307)
        self.assertRaises(webob.exc.HTTPClientError, abort, 400)
        self.assertRaises(webob.exc.HTTPUnauthorized, abort, 401)
        self.assertRaises(webob.exc.HTTPPaymentRequired, abort, 402)
        self.assertRaises(webob.exc.HTTPForbidden, abort, 403)
        self.assertRaises(webob.exc.HTTPNotFound, abort, 404)
        self.assertRaises(webob.exc.HTTPMethodNotAllowed, abort, 405)
        self.assertRaises(webob.exc.HTTPNotAcceptable, abort, 406)
        self.assertRaises(webob.exc.HTTPProxyAuthenticationRequired, abort, 407)
        self.assertRaises(webob.exc.HTTPRequestTimeout, abort, 408)
        self.assertRaises(webob.exc.HTTPConflict, abort, 409)
        self.assertRaises(webob.exc.HTTPGone, abort, 410)
        self.assertRaises(webob.exc.HTTPLengthRequired, abort, 411)
        self.assertRaises(webob.exc.HTTPPreconditionFailed, abort, 412)
        self.assertRaises(webob.exc.HTTPRequestEntityTooLarge, abort, 413)
        self.assertRaises(webob.exc.HTTPRequestURITooLong, abort, 414)
        self.assertRaises(webob.exc.HTTPUnsupportedMediaType, abort, 415)
        self.assertRaises(webob.exc.HTTPRequestRangeNotSatisfiable, abort, 416)
        self.assertRaises(webob.exc.HTTPExpectationFailed, abort, 417)
        self.assertRaises(webob.exc.HTTPInternalServerError, abort, 500)
        self.assertRaises(webob.exc.HTTPNotImplemented, abort, 501)
        self.assertRaises(webob.exc.HTTPBadGateway, abort, 502)
        self.assertRaises(webob.exc.HTTPServiceUnavailable, abort, 503)
        self.assertRaises(webob.exc.HTTPGatewayTimeout, abort, 504)
        self.assertRaises(webob.exc.HTTPVersionNotSupported, abort, 505)

        # Invalid use 500 as default.
        self.assertRaises(KeyError, abort, 0)
        self.assertRaises(KeyError, abort, 999999)
        self.assertRaises(KeyError, abort, 'foo')

    def test_import_string(self):
        self.assertEqual(import_string('webob.exc'), webob.exc)
        self.assertEqual(import_string('webob'), webob)

        self.assertEqual(import_string('dfasfasdfdsfsd', silent=True), None)
        self.assertEqual(import_string('webob.dfasfasdfdsfsd', silent=True), None)

        self.assertRaises(ImportError, import_string, 'dfasfasdfdsfsd')
        self.assertRaises(AttributeError, import_string, 'webob.dfasfasdfdsfsd')

    def test_to_utf8(self):
        res = to_utf8('ábcdéf'.decode('utf-8'))
        self.assertEqual(isinstance(res, str), True)

        res = to_utf8('abcdef')
        self.assertEqual(isinstance(res, str), True)

    def test_to_unicode(self):
        res = to_unicode(unicode('foo'))
        self.assertEqual(isinstance(res, unicode), True)

        res = to_unicode('foo')
        self.assertEqual(isinstance(res, unicode), True)

    def test_http_status_message(self):
        self.assertEqual(Response.http_status_message(404), 'Not Found')
        self.assertEqual(Response.http_status_message(500), 'Internal Server Error')
        self.assertRaises(KeyError, Response.http_status_message, 9999)


if __name__ == '__main__':
    test_base.main()
