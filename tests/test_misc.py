# -*- coding: utf-8 -*-
"""
Tests for webapp2 RequestHandler
"""
import unittest

from webtest import TestApp

import webob
import webob.exc

from webapp2 import RedirectHandler, RequestHandler, WSGIApplication, abort, get_exception_class, import_string


class TestMiscelaneous(unittest.TestCase):
    def test_get_exception_class(self):
        self.assertEqual(get_exception_class(200), webob.exc.HTTPOk)
        self.assertEqual(get_exception_class(201), webob.exc.HTTPCreated)
        self.assertEqual(get_exception_class(202), webob.exc.HTTPAccepted)
        self.assertEqual(get_exception_class(203), webob.exc.HTTPNonAuthoritativeInformation)
        self.assertEqual(get_exception_class(204), webob.exc.HTTPNoContent)
        self.assertEqual(get_exception_class(205), webob.exc.HTTPResetContent)
        self.assertEqual(get_exception_class(206), webob.exc.HTTPPartialContent)
        self.assertEqual(get_exception_class(300), webob.exc.HTTPMultipleChoices)
        self.assertEqual(get_exception_class(301), webob.exc.HTTPMovedPermanently)
        self.assertEqual(get_exception_class(302), webob.exc.HTTPFound)
        self.assertEqual(get_exception_class(303), webob.exc.HTTPSeeOther)
        self.assertEqual(get_exception_class(304), webob.exc.HTTPNotModified)
        self.assertEqual(get_exception_class(305), webob.exc.HTTPUseProxy)
        self.assertEqual(get_exception_class(307), webob.exc.HTTPTemporaryRedirect)
        self.assertEqual(get_exception_class(400), webob.exc.HTTPClientError)
        self.assertEqual(get_exception_class(401), webob.exc.HTTPUnauthorized)
        self.assertEqual(get_exception_class(402), webob.exc.HTTPPaymentRequired)
        self.assertEqual(get_exception_class(403), webob.exc.HTTPForbidden)
        self.assertEqual(get_exception_class(404), webob.exc.HTTPNotFound)
        self.assertEqual(get_exception_class(405), webob.exc.HTTPMethodNotAllowed)
        self.assertEqual(get_exception_class(406), webob.exc.HTTPNotAcceptable)
        self.assertEqual(get_exception_class(407), webob.exc.HTTPProxyAuthenticationRequired)
        self.assertEqual(get_exception_class(408), webob.exc.HTTPRequestTimeout)
        self.assertEqual(get_exception_class(409), webob.exc.HTTPConflict)
        self.assertEqual(get_exception_class(410), webob.exc.HTTPGone)
        self.assertEqual(get_exception_class(411), webob.exc.HTTPLengthRequired)
        self.assertEqual(get_exception_class(412), webob.exc.HTTPPreconditionFailed)
        self.assertEqual(get_exception_class(413), webob.exc.HTTPRequestEntityTooLarge)
        self.assertEqual(get_exception_class(414), webob.exc.HTTPRequestURITooLong)
        self.assertEqual(get_exception_class(415), webob.exc.HTTPUnsupportedMediaType)
        self.assertEqual(get_exception_class(416), webob.exc.HTTPRequestRangeNotSatisfiable)
        self.assertEqual(get_exception_class(417), webob.exc.HTTPExpectationFailed)
        self.assertEqual(get_exception_class(500), webob.exc.HTTPInternalServerError)
        self.assertEqual(get_exception_class(501), webob.exc.HTTPNotImplemented)
        self.assertEqual(get_exception_class(502), webob.exc.HTTPBadGateway)
        self.assertEqual(get_exception_class(503), webob.exc.HTTPServiceUnavailable)
        self.assertEqual(get_exception_class(504), webob.exc.HTTPGatewayTimeout)
        self.assertEqual(get_exception_class(505), webob.exc.HTTPVersionNotSupported)

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
        self.assertRaises(webob.exc.HTTPInternalServerError, abort, 0)
        self.assertRaises(webob.exc.HTTPInternalServerError, abort, 999999)
        self.assertRaises(webob.exc.HTTPInternalServerError, abort, 'foo')

    def test_import_string(self):
        self.assertEqual(import_string('webob.exc'), webob.exc)
        self.assertEqual(import_string('webob'), webob)

        self.assertEqual(import_string('dfasfasdfdsfsd', silent=True), None)
        self.assertEqual(import_string('webob.dfasfasdfdsfsd', silent=True), None)

        self.assertRaises(ImportError, import_string, 'dfasfasdfdsfsd')
        self.assertRaises(AttributeError, import_string, 'webob.dfasfasdfdsfsd')
