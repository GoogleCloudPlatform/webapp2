# -*- coding: utf-8 -*-
"""
Tests for webapp2 config
"""
import unittest

from nose.tools import assert_raises, raises

from webapp2 import Config


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
