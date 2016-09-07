# -*- coding: utf-8 -*-
# Copyright 2011 webapp2 AUTHORS.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from tests.gae import test_base
import webapp2
from webapp2_extras.appengine import users


def set_current_user(email, user_id, is_admin=False):
    os.environ['USER_EMAIL'] = email or ''
    os.environ['USER_ID'] = user_id or ''
    os.environ['USER_IS_ADMIN'] = '1' if is_admin else '0'


class LoginRequiredHandler(webapp2.RequestHandler):
    @users.login_required
    def get(self):
        self.response.write('You are logged in.')

    @users.login_required
    def post(self):
        self.response.write('You are logged in.')


class AdminRequiredHandler(webapp2.RequestHandler):
    @users.admin_required
    def get(self):
        self.response.write('You are admin.')

    @users.admin_required
    def post(self):
        self.response.write('You are admin.')


app = webapp2.WSGIApplication([
    ('/login_required', LoginRequiredHandler),
    ('/admin_required', AdminRequiredHandler),
])


class TestUsers(test_base.BaseTestCase):
    def test_login_required_allowed(self):
        set_current_user('foo@bar.com', 'foo@bar.com')
        req = webapp2.Request.blank('/login_required')

        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 200)
        self.assertEqual(rsp.body, 'You are logged in.')

    def test_login_required_302(self):
        req = webapp2.Request.blank('/login_required')

        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 302)
        self.assertEqual(
            rsp.headers.get('Location'),
            'https://www.google.com/accounts/Login?continue='
            'http%3A//localhost/login_required'
        )

    def test_login_required_post(self):
        req = webapp2.Request.blank('/login_required')
        req.method = 'POST'

        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 400)

    def test_admin_required_allowed(self):
        set_current_user('foo@bar.com', 'foo@bar.com', is_admin=True)
        req = webapp2.Request.blank('/admin_required')

        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 200)
        self.assertEqual(rsp.body, 'You are admin.')

    def test_admin_required_not_admin(self):
        set_current_user('foo@bar.com', 'foo@bar.com')
        req = webapp2.Request.blank('/admin_required')

        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 403)

    def test_admin_required_302(self):
        req = webapp2.Request.blank('/admin_required')

        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 302)
        self.assertEqual(
            rsp.headers.get('Location'),
            'https://www.google.com/accounts/Login?continue='
            'http%3A//localhost/admin_required'
        )

    def test_admin_required_post(self):
        req = webapp2.Request.blank('/admin_required')
        req.method = 'POST'

        rsp = req.get_response(app)
        self.assertEqual(rsp.status_int, 400)


if __name__ == '__main__':
    test_base.main()
