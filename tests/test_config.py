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
        config = Config()

        from resources.template import default_config as template_config
        from resources.i18n import default_config as i18n_config

        assert config.load_and_get('resources.template', 'templates_dir') == template_config['templates_dir']
        assert config.load_and_get('resources.i18n', 'locale') == i18n_config['locale']
        assert config.load_and_get('resources.i18n', 'timezone') == i18n_config['timezone']

    def test_default_config_with_non_existing_key(self):
        config = Config()

        from resources.i18n import default_config as i18n_config

        # In the first time the module config will be loaded normally.
        assert config.load_and_get('resources.i18n', 'locale') == i18n_config['locale']

        # In the second time it won't be loaded, but won't find the value and then use the default.
        assert config.load_and_get('resources.i18n', 'i_dont_exist', 'foo') == 'foo'

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

        assert config.load_and_get('resources.template', 'templates_dir') == 'apps/templates'
        assert config.load_and_get('resources.i18n', 'locale') == 'pt_BR'
        assert config.load_and_get('resources.i18n', 'timezone') == 'America/Sao_Paulo'

    def test_override_config2(self):
        config = Config({
            'resources.i18n': {
                'timezone': 'America/Sao_Paulo',
            },
        })

        assert config.load_and_get('resources.i18n', 'locale') == 'en_US'
        assert config.load_and_get('resources.i18n', 'timezone') == 'America/Sao_Paulo'

    def test_get(self):
        config = Config({'foo': {
            'bar': 'baz',
        }})

        assert config.load_and_get('foo', 'bar') == 'baz'

    def test_get_with_default(self):
        config = Config()

        assert config.load_and_get('resources.i18n', 'bar', 'baz') == 'baz'

    def test_get_with_default_and_none(self):
        config = Config({'foo': {
            'bar': None,
        }})

        assert config.load_and_get('foo', 'bar', 'ooops') is None

    def test_get_with_default_and_module_load(self):
        config = Config()
        assert config.load_and_get('resources.i18n', 'locale') == 'en_US'
        assert config.load_and_get('resources.i18n', 'locale', 'foo') == 'en_US'

    @raises(KeyError)
    def test_required_config(self):
        config = Config()
        config.load_and_get('resources.i18n', 'required')

    @raises(KeyError)
    def test_missing_module(self):
        config = Config()
        assert config.load_and_get('i_dont_exist', 'i_dont_exist') == 'baz'

    @raises(KeyError)
    def test_missing_module2(self):
        config = Config()
        assert config.load_and_get('i_dont_exist') == 'baz'

    @raises(KeyError)
    def test_missing_key(self):
        config = Config()
        config.load_and_get('resources.i18n', 'i_dont_exist')

    @raises(KeyError)
    def test_missing_default_config(self):
        config = Config()
        assert config.load_and_get('webapp2', 'foo') == 'baz'

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
