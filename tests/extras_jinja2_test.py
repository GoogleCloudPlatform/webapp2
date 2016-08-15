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
from webapp2_extras import jinja2


current_dir = os.path.abspath(os.path.dirname(__file__))
template_path = os.path.join(current_dir, 'resources', 'jinja2_templates')
compiled_path = os.path.join(current_dir, 'resources',
                             'jinja2_templates_compiled')


class TestJinja2(unittest.TestCase):
    def test_render_template_with_i18n(self):
        app = webapp2.WSGIApplication(config={
            'webapp2_extras.jinja2': {
                'template_path': template_path,
                'environment_args': {
                    'autoescape': True,
                    'extensions': [
                        'jinja2.ext.autoescape',
                        'jinja2.ext.with_',
                        'jinja2.ext.i18n',
                    ],
                },
            },
        })
        req = webapp2.Request.blank('/')
        app.set_globals(app=app, request=req)
        j = jinja2.Jinja2(app)

        message = 'Hello, i18n World!'
        res = j.render_template('template2.html', message=message)
        self.assertEqual(res, message)

    def test_render_template_globals_filters(self):
        app = webapp2.WSGIApplication(config={
            'webapp2_extras.jinja2': {
                'template_path': template_path,
                'globals': dict(foo='fooglobal'),
                'filters': dict(foo=lambda x: x + '-foofilter'),
            },
        })
        req = webapp2.Request.blank('/')
        app.set_globals(app=app, request=req)
        j = jinja2.Jinja2(app)

        message = 'fooglobal-foofilter'
        res = j.render_template('template3.html', message=message)
        self.assertEqual(res, message)

    def test_render_template_force_compiled(self):
        app = webapp2.WSGIApplication(config={
            'webapp2_extras.jinja2': {
                'template_path': template_path,
                'compiled_path': compiled_path,
                'force_compiled': True,
            }
        })
        req = webapp2.Request.blank('/')
        app.set_globals(app=app, request=req)
        j = jinja2.Jinja2(app)

        message = 'Hello, World!'
        res = j.render_template('template1.html', message=message)
        self.assertEqual(res, message)

    def test_get_template_attribute(self):
        app = webapp2.WSGIApplication(config={
            'webapp2_extras.jinja2': {
                'template_path': template_path,
            }
        })
        j = jinja2.Jinja2(app)
        hello = j.get_template_attribute('hello.html', 'hello')
        self.assertEqual(hello('World'), 'Hello, World!')

    def test_set_jinja2(self):
        app = webapp2.WSGIApplication()
        self.assertEqual(len(app.registry), 0)
        jinja2.set_jinja2(jinja2.Jinja2(app), app=app)
        self.assertEqual(len(app.registry), 1)
        j = jinja2.get_jinja2(app=app)
        self.assertTrue(isinstance(j, jinja2.Jinja2))

    def test_get_jinja2(self):
        app = webapp2.WSGIApplication()
        self.assertEqual(len(app.registry), 0)
        j = jinja2.get_jinja2(app=app)
        self.assertEqual(len(app.registry), 1)
        self.assertTrue(isinstance(j, jinja2.Jinja2))


if __name__ == '__main__':
    unittest.main()
