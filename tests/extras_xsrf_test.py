# -*- coding: utf-8 -*-

import base64

from webapp2_extras import xsrf

import test_base


class TestXSRFToken(test_base.BaseTestCase):
    def test_verify_timeout(self):
        token = xsrf.XSRFToken('user@example.com',
                               'secret',
                               current_time=1354160000)
        token_string = token.generate_token_string()
        token.verify_token_string(token_string,
                                  timeout=10,
                                  current_time=1354160010)
        self.assertRaises(xsrf.XSRFTokenExpiredException,
                          token.verify_token_string,
                          token_string,
                          timeout=10,
                          current_time=1354160011)

    def test_verify_no_action(self):
        token = xsrf.XSRFToken('user@example.com',
                               'secret',
                               current_time=1354160000)
        token_string = token.generate_token_string()
        token.verify_token_string(token_string)
        self.assertRaises(
            xsrf.XSRFTokenInvalid,
            token.verify_token_string,
            xsrf.XSRFToken('user@example.com',
                           'differentsecret',
                           current_time=1354160000).generate_token_string())
        self.assertRaises(
            xsrf.XSRFTokenInvalid,
            token.verify_token_string,
            xsrf.XSRFToken('user@example.com',
                           'secret',
                           current_time=1354160000).generate_token_string(
                               'action'))

    def test_verify_action(self):
        token = xsrf.XSRFToken('user@example.com',
                               'secret',
                               current_time=1354160000)
        token_string = token.generate_token_string('action')
        token.verify_token_string(token_string, 'action')
        self.assertRaises(
            xsrf.XSRFTokenInvalid,
            token.verify_token_string,
            xsrf.XSRFToken('user@example.com',
                           'differentsecret',
                           current_time=1354160000).generate_token_string())

    def test_verify_substring(self):
        """Tests that a substring of the correct token fails to verify."""
        token = xsrf.XSRFToken('user@example.com',
                               'secret',
                               current_time=1354160000)
        token_string = token.generate_token_string()
        test_token, test_time = base64.urlsafe_b64decode(token_string).split('|')
        test_string = base64.urlsafe_b64encode('|'.join([test_token[:-1],
                                                         test_time]))
        self.assertRaises(xsrf.XSRFTokenInvalid,
                          token.verify_token_string,
                          test_string)

    def test_verify_bad_base_64(self):
        token = xsrf.XSRFToken('user@example.com',
                               'secret')
        self.assertRaises(
            xsrf.XSRFTokenMalformed,
            token.verify_token_string,
            'wrong!!')

    def test_verify_no_delimiter(self):
        token = xsrf.XSRFToken('user@example.com',
                               'secret')
        self.assertRaises(
            xsrf.XSRFTokenMalformed,
            token.verify_token_string,
            base64.b64encode('NODELIMITER'))

    def test_verify_time_not_int(self):
        token = xsrf.XSRFToken('user@example.com',
                               'secret')
        self.assertRaises(
            xsrf.XSRFTokenMalformed,
            token.verify_token_string,
            base64.b64encode('NODE|NOTINT'))

if __name__ == '__main__':
    test_base.main()
