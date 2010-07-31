# -*- coding: utf-8 -*-
"""
Tests for webapp2 config
"""
import unittest

from nose.tools import assert_raises, raises

from webapp2 import Config, WSGIApplication, RequestHandler, REQUIRED_VALUE


class TestConfig(unittest.TestCase):
    def test_get_existing_keys(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

    def test_get_existing_keys_from_default(self):
        config = Config({}, {'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

    def test_get_non_existing_keys(self):
        config = Config()

        assert config.get('foo', 'bar') is None

    def test_get_dict_existing_keys(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config.get('foo') == {
            'bar': 'baz',
            'doo': 'ding',
        }

    def test_get_dict_non_existing_keys(self):
        config = Config()

        assert config.get('bar') is None

    def test_get_with_default(self):
        config = Config()

        assert config.get('foo', 'bar', 'ooops') == 'ooops'
        assert config.get('foo', 'doo', 'wooo') == 'wooo'

    def test_get_with_default_and_none(self):
        config = Config({'foo': {
            'bar': None,
        }})

        assert config.get('foo', 'bar', 'ooops') is None

    def test_update(self):
        config = Config({'foo': {
            'bar': 'baz',
            'doo': 'ding',
        }})

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

        config.update('foo', {'bar': 'other'})

        assert config.get('foo', 'bar') == 'other'
        assert config.get('foo', 'doo') == 'ding'

    def test_setdefault(self):
        config = Config()

        assert config.get('foo') is None

        config.setdefault('foo', {
            'bar': 'baz',
            'doo': 'ding',
        })

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

    def test_setdefault2(self):
        config = Config({'foo': {
            'bar': 'baz',
        }})

        assert config.get('foo') == {
            'bar': 'baz',
        }

        config.setdefault('foo', {
            'bar': 'wooo',
            'doo': 'ding',
        })

        assert config.get('foo', 'bar') == 'baz'
        assert config.get('foo', 'doo') == 'ding'

    def test_setitem(self):
        config = Config()

        def setitem(key, value):
            config[key] = value
            return config

        assert setitem('foo', {'bar': 'baz'}) == {'foo': {'bar': 'baz'}}

    def test_init_no_dict_values(self):
        assert_raises(AssertionError, Config, {'foo': 'bar'})
        assert_raises(AssertionError, Config, {'foo': None})
        assert_raises(AssertionError, Config, 'foo')

    def test_init_no_dict_default(self):
        assert_raises(AssertionError, Config, {}, {'foo': 'bar'})
        assert_raises(AssertionError, Config, {}, {'foo': None})
        assert_raises(AssertionError, Config, {}, 'foo')

    def test_update_no_dict_values(self):
        config = Config()

        assert_raises(AssertionError, config.update, {'foo': 'bar'}, 'baz')
        assert_raises(AssertionError, config.update, {'foo': None}, 'baz')
        assert_raises(AssertionError, config.update, 'foo', 'bar')

    def test_setdefault_no_dict_values(self):
        config = Config()

        assert_raises(AssertionError, config.setdefault, 'foo', 'bar')
        assert_raises(AssertionError, config.setdefault, 'foo', None)

    def test_setitem_no_dict_values(self):
        config = Config()

        def setitem(key, value):
            config[key] = value
            return config

        assert_raises(AssertionError, setitem, 'foo', 'bar')
        assert_raises(AssertionError, setitem, 'foo', None)


class TestGetConfig(unittest.TestCase):
    def test_default_config(self):
        app = WSGIApplication()

        from resources.template import default_config as jinja2_config
        from resources.i18n import default_config as i18n_config

        assert app.get_config('resources.template', 'templates_dir') == jinja2_config['templates_dir']
        assert app.get_config('resources.i18n', 'locale') == i18n_config['locale']
        assert app.get_config('resources.i18n', 'timezone') == i18n_config['timezone']

    def test_default_config_with_non_existing_key(self):
        app = WSGIApplication()

        from resources.i18n import default_config as i18n_config

        # In the first time the module config will be loaded normally.
        assert app.get_config('resources.i18n', 'locale') == i18n_config['locale']

        # In the second time it won't be loaded, but won't find the value and then use the default.
        assert app.get_config('resources.i18n', 'i_dont_exist', 'foo') == 'foo'

    def test_override_config(self):
        app = WSGIApplication(config={
            'resources.template': {
                'templates_dir': 'apps/templates'
            },
            'resources.i18n': {
                'locale': 'pt_BR',
                'timezone': 'America/Sao_Paulo',
            },
        })

        assert app.get_config('resources.template', 'templates_dir') == 'apps/templates'
        assert app.get_config('resources.i18n', 'locale') == 'pt_BR'
        assert app.get_config('resources.i18n', 'timezone') == 'America/Sao_Paulo'

    def test_override_config2(self):
        app = WSGIApplication(config={
            'resources.i18n': {
                'timezone': 'America/Sao_Paulo',
            },
        })

        assert app.get_config('resources.i18n', 'locale') == 'en_US'
        assert app.get_config('resources.i18n', 'timezone') == 'America/Sao_Paulo'

    def test_get(self):
        app = WSGIApplication(config={'foo': {
            'bar': 'baz',
        }})

        assert app.get_config('foo', 'bar') == 'baz'

    def test_get_with_default(self):
        app = WSGIApplication()

        assert app.get_config('resources.i18n', 'bar', 'baz') == 'baz'

    def test_get_with_default_and_none(self):
        app = WSGIApplication(config={'foo': {
            'bar': None,
        }})

        assert app.get_config('foo', 'bar', 'ooops') is None

    def test_get_with_default_and_module_load(self):
        app = WSGIApplication()
        assert app.get_config('resources.i18n', 'locale') == 'en_US'

        app = WSGIApplication()
        assert app.get_config('resources.i18n', 'locale', 'foo') == 'en_US'

    @raises(KeyError)
    def test_required_config(self):
        app = WSGIApplication()
        app.get_config('resources.i18n', 'required')

    @raises(KeyError)
    def test_missing_module(self):
        app = WSGIApplication()
        assert app.get_config('i_dont_exist', 'i_dont_exist') == 'baz'

    @raises(KeyError)
    def test_missing_module2(self):
        app = WSGIApplication()
        assert app.get_config('i_dont_exist') == 'baz'

    @raises(KeyError)
    def test_missing_key(self):
        app = WSGIApplication()
        app.get_config('resources.i18n', 'i_dont_exist')

    @raises(KeyError)
    def test_missing_default_config(self):
        app = WSGIApplication()
        assert app.get_config('webapp2', 'foo') == 'baz'

    def test_request_handler_get_config(self):
        app = WSGIApplication()

        handler = RequestHandler(app, None, None)

        assert handler.get_config('resources.i18n', 'locale') == 'en_US'
        assert handler.get_config('resources.i18n', 'locale', 'foo') == 'en_US'
        assert handler.get_config('resources.i18n') == {
            'locale': 'en_US',
            'timezone': 'America/Chicago',
            'required': REQUIRED_VALUE,
        }
