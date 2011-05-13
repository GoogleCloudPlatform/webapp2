# -*- coding: utf-8 -*-
import os

import webapp2
from webapp2_extras import config
from webapp2_extras import jinja2

import test_base

current_dir = os.path.abspath(os.path.dirname(__file__))
template_path = os.path.join(current_dir, 'resources', 'templates')
compiled_path = os.path.join(current_dir, 'resources', 'templates_compiled')

class TestJinja2(test_base.BaseTestCase):
    def test_render_template_with_i18n(self):
        app = webapp2.WSGIApplication(debug=True)
        app.config = config.Config({
            'webapp2_extras.jinja2': {
                'template_path': template_path,
                'compiled_path': compiled_path,
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

    def test_render_template_force_compiled(self):
        app = webapp2.WSGIApplication(debug=True)
        app.config = config.Config({
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
        app = webapp2.WSGIApplication(debug=True)
        app.config = config.Config({
            'webapp2_extras.jinja2': {
                'template_path': template_path,
                'compiled_path': compiled_path,
            }
        })
        j = jinja2.Jinja2(app)
        hello = j.get_template_attribute('hello.html', 'hello')
        self.assertEqual(hello('World'), 'Hello, World!')

    def get_jinja2(self):
        app = webapp2.WSGIApplication(debug=True)
        j = jinja2.get_jinja2(app=app)
        self.assertTrue(isinstance(j, jinja2.Jinja2))


if __name__ == '__main__':
    test_base.main()
