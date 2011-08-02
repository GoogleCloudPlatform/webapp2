import ConfigParser
import os
import textwrap
import StringIO
import sys
import unittest
import StringIO

import test_utils

from manage.config import Config


class TestConfig(test_utils.BaseTestCase):
    def get_fp(self, config):
        return StringIO.StringIO(textwrap.dedent(config))

    def test_get(self):
        fp = self.get_fp("""\
        [DEFAULT]
        foo = bar

        [section_1]
        baz = ding
        """)
        config = Config()
        config.readfp(fp)

        self.assertEqual(config.get('section_1', 'foo'), 'bar')
        self.assertEqual(config.get('section_1', 'baz'), 'ding')

        # Invalid key.
        self.assertEqual(config.get('section_1', 'invalid'), None)

    def test_getboolean(self):
        fp = self.get_fp("""\
        [DEFAULT]
        true_1 = 1
        true_2 = yes
        false_1 = 0
        false_2 = no

        [section_1]
        true_3 = on
        true_4 = true
        false_3 = off
        false_4 = false
        invalid = bar
        """)
        config = Config()
        config.readfp(fp)

        self.assertEqual(config.getboolean('section_1', 'true_1'), True)
        self.assertEqual(config.getboolean('section_1', 'true_2'), True)
        self.assertEqual(config.getboolean('section_1', 'true_3'), True)
        self.assertEqual(config.getboolean('section_1', 'true_4'), True)
        self.assertEqual(config.getboolean('section_1', 'false_1'), False)
        self.assertEqual(config.getboolean('section_1', 'false_2'), False)
        self.assertEqual(config.getboolean('section_1', 'false_3'), False)
        self.assertEqual(config.getboolean('section_1', 'false_4'), False)

        # Invalid boolean.
        self.assertEqual(config.getboolean('section_1', 'invalid'), None)

    def test_getfloat(self):
        fp = self.get_fp("""\
        [DEFAULT]
        foo = 0.1

        [section_1]
        baz = 0.2
        invalid = bar
        """)
        config = Config()
        config.readfp(fp)

        self.assertEqual(config.getfloat('section_1', 'foo'), 0.1)
        self.assertEqual(config.getfloat('section_1', 'baz'), 0.2)

        # Invalid float.
        self.assertEqual(config.getboolean('section_1', 'invalid'), None)

    def test_getint(self):
        fp = self.get_fp("""\
        [DEFAULT]
        foo = 999

        [section_1]
        baz = 1999
        invalid = bar
        """)
        config = Config()
        config.readfp(fp)

        self.assertEqual(config.getint('section_1', 'foo'), 999)
        self.assertEqual(config.getint('section_1', 'baz'), 1999)

        # Invalid int.
        self.assertEqual(config.getboolean('section_1', 'invalid'), None)

    def test_getlist(self):
        fp = self.get_fp("""\
        [DEFAULT]
        animals =
            rhino
            rhino
            hamster
            hamster
            goat
            goat

        [section_1]
        fruits =
            orange
            watermellow
            grape
        """)
        config = Config()
        config.readfp(fp)

        # Non-unique values.
        self.assertEqual(config.getlist('section_1', 'animals'), [
            'rhino',
            'rhino',
            'hamster',
            'hamster',
            'goat',
            'goat',
        ])
        self.assertEqual(config.getlist('section_1', 'fruits'), [
            'orange',
            'watermellow',
            'grape',
        ])

        # Unique values.
        self.assertEqual(config.getlist('section_1', 'animals', unique=True), [
            'rhino',
            'hamster',
            'goat',
        ])

    def test_interpolation(self):
        fp = self.get_fp("""\
        [DEFAULT]
        path = /path/to/%(path_name)s

        [section_1]
        path_name = foo
        path_1 = /special%(path)s
        path_2 = /special/%(path_name)s

        [section_2]
        path_name = bar

        [section_3]
        path_1 = /path/to/%(section_1|path_name)s
        path_2 = /path/to/%(section_2|path_name)s
        path_3 = /%(section_1|path_name)s/%(section_2|path_name)s/%(section_1|path_name)s/%(section_2|path_name)s
        path_error_1 = /path/to/%(section_3|path_error_1)s
        path_error_2 = /path/to/%(section_3|path_error_3)s
        path_error_3 = /path/to/%(section_3|path_error_2)s
        path_not_really = /path/to/%(foo
        """)
        config = Config()
        config.readfp(fp)

        self.assertEqual(config.get('section_1', 'path'), '/path/to/foo')
        self.assertEqual(config.get('section_1', 'path_1'), '/special/path/to/foo')
        self.assertEqual(config.get('section_1', 'path_2'), '/special/foo')
        self.assertEqual(config.get('section_2', 'path'), '/path/to/bar')

        self.assertEqual(config.get('section_3', 'path_1'), '/path/to/foo')
        self.assertEqual(config.get('section_3', 'path_2'), '/path/to/bar')
        self.assertEqual(config.get('section_3', 'path_3'), '/foo/bar/foo/bar')

        # Failed interpolation (recursive)
        self.assertRaises(ConfigParser.InterpolationError, config.get,
            'section_3', 'path_error_1')
        self.assertRaises(ConfigParser.InterpolationError, config.get,
            'section_3', 'path_error_2')
        self.assertRaises(ConfigParser.InterpolationError, config.get,
            'section_3', 'path_error_3')

        self.assertEqual(config.get('section_3', 'path_not_really'), '/path/to/%(foo')


if __name__ == '__main__':
    test_base.main()
