# -*- coding: utf-8 -*-
"""
Tests for webapp2.Config
"""
import unittest

from webapp2 import (Config, WSGIApplication, Request, RequestHandler,
    REQUIRED_VALUE)

import test_base


class TestConfig(test_base.BaseTestCase):
    def tearDown(self):
        pass

    def test_get(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get('foo'), {
            'bar': 'baz',
            'doo': 'ding',
        })

        self.assertEqual(config.get('bar'), {})

    def test_get_existing_keys(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get_config('foo', 'bar'), 'baz')
        self.assertEqual(config.get_config('foo', 'doo'), 'ding')

    def test_get_existing_keys_from_default(self):
        config = Config({}, {'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get_config('foo', 'bar'), 'baz')
        self.assertEqual(config.get_config('foo', 'doo'), 'ding')

    def test_get_non_existing_keys(self):
        config = Config()

        self.assertRaises(KeyError, config.get_config, 'foo', 'bar')

    def test_get_dict_existing_keys(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get_config('foo'), {
            'bar': 'baz',
            'doo': 'ding',
        })

    def test_get_dict_non_existing_keys(self):
        config = Config()

        self.assertRaises(KeyError, config.get_config, 'bar')

    def test_get_with_default(self):
        config = Config()

        self.assertRaises(KeyError, config.get_config, 'foo', 'bar', 'ooops')
        self.assertRaises(KeyError, config.get_config, 'foo', 'doo', 'wooo')

    def test_get_with_default_and_none(self):
        config = Config({'foo': {
            'bar': None,
        }})

        self.assertEqual(config.get_config('foo', 'bar', 'ooops'), None)

    def test_update(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        self.assertEqual(config.get_config('foo', 'bar'), 'baz')
        self.assertEqual(config.get_config('foo', 'doo'), 'ding')

        config.update('foo', {'bar': 'other'})

        self.assertEqual(config.get_config('foo', 'bar'), 'other')
        self.assertEqual(config.get_config('foo', 'doo'), 'ding')

    def test_setdefault(self):
        config = Config()

        self.assertRaises(KeyError, config.get_config, 'foo')

        config.setdefault('foo', {
            'bar': 'baz',
            'doo': 'ding',
        })

        self.assertEqual(config.get_config('foo', 'bar'), 'baz')
        self.assertEqual(config.get_config('foo', 'doo'), 'ding')

    def test_setdefault2(self):
        config = Config({'foo': {
            'bar': 'baz',
        }})

        self.assertEqual(config.get_config('foo'), {
            'bar': 'baz',
        })

        config.setdefault('foo', {
            'bar': 'wooo',
            'doo': 'ding',
        })

        self.assertEqual(config.get_config('foo', 'bar'), 'baz')
        self.assertEqual(config.get_config('foo', 'doo'), 'ding')

    def test_setitem(self):
        config = Config()
        config['foo'] = {'bar': 'baz'}

        self.assertEqual(config, {'foo': {'bar': 'baz'}})
        self.assertEqual(config['foo'], {'bar': 'baz'})

    def test_init_no_dict_values(self):
        self.assertRaises(AssertionError, Config, {'foo': 'bar'})
        self.assertRaises(AssertionError, Config, {'foo': None})
        self.assertRaises(AssertionError, Config, 'foo')

    def test_init_no_dict_default(self):
        self.assertRaises(AssertionError, Config, {}, {'foo': 'bar'})
        self.assertRaises(AssertionError, Config, {}, {'foo': None})
        self.assertRaises(AssertionError, Config, {}, 'foo')

    def test_update_no_dict_values(self):
        config = Config()

        self.assertRaises(AssertionError, config.update, {'foo': 'bar'}, 'baz')
        self.assertRaises(AssertionError, config.update, {'foo': None}, 'baz')
        self.assertRaises(AssertionError, config.update, 'foo', 'bar')

    def test_setdefault_no_dict_values(self):
        config = Config()

        self.assertRaises(AssertionError, config.setdefault, 'foo', 'bar')
        self.assertRaises(AssertionError, config.setdefault, 'foo', None)

    def test_setitem_no_dict_values(self):
        config = Config()

        def setitem(key, value):
            config[key] = value
            return config

        self.assertRaises(AssertionError, setitem, 'foo', 'bar')
        self.assertRaises(AssertionError, setitem, 'foo', None)


class TestLoadConfig(test_base.BaseTestCase):
    def tearDown(self):
        pass

    def test_default_config(self):
        config = Config()

        from resources.template import default_config as template_config
        from resources.i18n import default_config as i18n_config

        self.assertEqual(config.get_config('resources.template', 'templates_dir'), template_config['templates_dir'])
        self.assertEqual(config.get_config('resources.i18n', 'locale'), i18n_config['locale'])
        self.assertEqual(config.get_config('resources.i18n', 'timezone'), i18n_config['timezone'])

    def test_default_config_with_non_existing_key(self):
        config = Config()

        from resources.i18n import default_config as i18n_config

        # In the first time the module config will be loaded normally.
        self.assertEqual(config.get_config('resources.i18n', 'locale'), i18n_config['locale'])

        # In the second time it won't be loaded, but won't find the value and then use the default.
        self.assertEqual(config.get_config('resources.i18n', 'i_dont_exist', 'foo'), 'foo')

    def test_override_config(self):
        config = Config({
            'resources.template': {
                'templates_dir': 'apps/templates'
            },
            'resources.i18n': {
                'locale': 'pt_BR',
                'timezone': 'America/Sao_Paulo',
            },
        })

        self.assertEqual(config.get_config('resources.template', 'templates_dir'), 'apps/templates')
        self.assertEqual(config.get_config('resources.i18n', 'locale'), 'pt_BR')
        self.assertEqual(config.get_config('resources.i18n', 'timezone'), 'America/Sao_Paulo')

    def test_override_config2(self):
        config = Config({
            'resources.i18n': {
                'timezone': 'America/Sao_Paulo',
            },
        })

        self.assertEqual(config.get_config('resources.i18n', 'locale'), 'en_US')
        self.assertEqual(config.get_config('resources.i18n', 'timezone'), 'America/Sao_Paulo')

    def test_get(self):
        config = Config({'foo': {
            'bar': 'baz',
        }})

        self.assertEqual(config.get_config('foo', 'bar'), 'baz')

    def test_get_with_default(self):
        config = Config()

        self.assertEqual(config.get_config('resources.i18n', 'bar', 'baz'), 'baz')

    def test_get_with_default_and_none(self):
        config = Config({'foo': {
            'bar': None,
        }})

        self.assertEqual(config.get_config('foo', 'bar', 'ooops'), None)

    def test_get_with_default_and_module_load(self):
        config = Config()
        self.assertEqual(config.get_config('resources.i18n', 'locale'), 'en_US')
        self.assertEqual(config.get_config('resources.i18n', 'locale', 'foo'), 'en_US')

    def test_required_config(self):
        config = Config()
        self.assertRaises(KeyError, config.get_config, 'resources.i18n', 'foo')

    def test_missing_module(self):
        config = Config()
        self.assertRaises(KeyError, config.get_config, 'i_dont_exist', 'i_dont_exist')

    def test_missing_module2(self):
        config = Config()
        self.assertRaises(KeyError, config.get_config, 'i_dont_exist')

    def test_missing_key(self):
        config = Config()
        self.assertRaises(KeyError, config.get_config, 'resources.i18n', 'i_dont_exist')

    def test_missing_default_config(self):
        config = Config()
        self.assertRaises(KeyError, config.get_config, 'tipfy', 'foo')

    def test_app_get_config(self):
        app = WSGIApplication()

        self.assertEqual(app.get_config('resources.i18n', 'locale'), 'en_US')
        self.assertEqual(app.get_config('resources.i18n', 'locale', 'foo'), 'en_US')
        self.assertEqual(app.get_config('resources.i18n'), {
            'locale': 'en_US',
            'timezone': 'America/Chicago',
            'required': REQUIRED_VALUE,
        })

    def test_request_handler_get_config(self):
        app = WSGIApplication()
        request = Request.blank('http://localhost:80/')
        request.app = app

        handler = RequestHandler(request, None)
        handler.app = app

        self.assertEqual(handler.get_config('resources.i18n', 'locale'), 'en_US')
        self.assertEqual(handler.get_config('resources.i18n', 'locale', 'foo'), 'en_US')
        self.assertEqual(handler.get_config('resources.i18n'), {
            'locale': 'en_US',
            'timezone': 'America/Chicago',
            'required': REQUIRED_VALUE,
        })


class TestLoadConfigGetItem(test_base.BaseTestCase):
    def tearDown(self):
        pass

    def test_default_config(self):
        config = Config()

        from resources.template import default_config as template_config
        from resources.i18n import default_config as i18n_config

        self.assertEqual(config['resources.template']['templates_dir'], template_config['templates_dir'])
        self.assertEqual(config['resources.i18n']['locale'], i18n_config['locale'])
        self.assertEqual(config['resources.i18n']['timezone'], i18n_config['timezone'])

    def test_default_config_with_non_existing_key(self):
        config = Config()

        from resources.i18n import default_config as i18n_config

        # In the first time the module config will be loaded normally.
        self.assertEqual(config['resources.i18n']['locale'], i18n_config['locale'])

        # In the second time it won't be loaded, but won't find the value and then use the default.
        self.assertEqual(config['resources.i18n'].get('i_dont_exist', 'foo'), 'foo')

    def test_override_config(self):
        config = Config({
            'resources.template': {
                'templates_dir': 'apps/templates'
            },
            'resources.i18n': {
                'locale': 'pt_BR',
                'timezone': 'America/Sao_Paulo',
            },
        })

        self.assertEqual(config['resources.template']['templates_dir'], 'apps/templates')
        self.assertEqual(config['resources.i18n']['locale'], 'pt_BR')
        self.assertEqual(config['resources.i18n']['timezone'], 'America/Sao_Paulo')

    def test_override_config2(self):
        config = Config({
            'resources.i18n': {
                'timezone': 'America/Sao_Paulo',
            },
        })

        self.assertEqual(config['resources.i18n']['locale'], 'en_US')
        self.assertEqual(config['resources.i18n']['timezone'], 'America/Sao_Paulo')

    def test_get(self):
        config = Config({'foo': {
            'bar': 'baz',
        }})

        self.assertEqual(config['foo']['bar'], 'baz')

    def test_get_with_default(self):
        config = Config()

        self.assertEqual(config['resources.i18n'].get('bar', 'baz'), 'baz')

    def test_get_with_default_and_none(self):
        config = Config({'foo': {
            'bar': None,
        }})

        self.assertEqual(config['foo'].get('bar', 'ooops'), None)

    def test_get_with_default_and_module_load(self):
        config = Config()
        self.assertEqual(config['resources.i18n']['locale'], 'en_US')
        self.assertEqual(config['resources.i18n'].get('locale', 'foo'), 'en_US')

    def test_required_config(self):
        config = Config()
        self.assertRaises(KeyError, config['resources.i18n'].__getitem__, 'foo')
        self.assertRaises(KeyError, config['resources.i18n'].__getitem__, 'required')

    def test_missing_module(self):
        config = Config()
        self.assertRaises(KeyError, config.__getitem__, 'i_dont_exist')

    def test_missing_key(self):
        config = Config()
        self.assertRaises(KeyError, config['resources.i18n'].__getitem__, 'i_dont_exist')


if __name__ == '__main__':
    test_base.main()
