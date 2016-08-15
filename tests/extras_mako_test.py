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
import unittest

import webapp2
from webapp2_extras import mako


current_dir = os.path.abspath(os.path.dirname(__file__))
template_path = os.path.join(current_dir, 'resources', 'mako_templates')


class TestMako(unittest.TestCase):
    def test_render_template(self):
        app = webapp2.WSGIApplication(config={
            'webapp2_extras.mako': {
                'template_path': template_path,
            },
        })
        req = webapp2.Request.blank('/')
        app.set_globals(app=app, request=req)
        m = mako.Mako(app)

        message = 'Hello, World!'
        res = m.render_template('template1.html', message=message)
        self.assertEqual(res, message + '\n')

    def test_set_mako(self):
        app = webapp2.WSGIApplication()
        self.assertEqual(len(app.registry), 0)
        mako.set_mako(mako.Mako(app), app=app)
        self.assertEqual(len(app.registry), 1)
        j = mako.get_mako(app=app)
        self.assertTrue(isinstance(j, mako.Mako))

    def test_get_mako(self):
        app = webapp2.WSGIApplication()
        self.assertEqual(len(app.registry), 0)
        j = mako.get_mako(app=app)
        self.assertEqual(len(app.registry), 1)
        self.assertTrue(isinstance(j, mako.Mako))


if __name__ == '__main__':
    unittest.main()
