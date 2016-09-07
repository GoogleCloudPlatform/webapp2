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

import re
import unittest

import six
from webapp2_extras import security


class TestSecurity(unittest.TestCase):
    def test_generate_random_string(self):
        self.assertRaises(ValueError, security.generate_random_string, None)
        self.assertRaises(ValueError, security.generate_random_string, 0)
        self.assertRaises(ValueError, security.generate_random_string, -1)
        self.assertRaises(ValueError, security.generate_random_string, 1, 1)

        token = security.generate_random_string(16)
        self.assertTrue(re.match(r'^\w{16}$', token) is not None)

        token = security.generate_random_string(32)
        self.assertTrue(re.match(r'^\w{32}$', token) is not None)

        token = security.generate_random_string(64)
        self.assertTrue(re.match(r'^\w{64}$', token) is not None)

        token = security.generate_random_string(128)
        self.assertTrue(re.match(r'^\w{128}$', token) is not None)

    def test_create_check_password_hash(self):
        self.assertRaises(TypeError, security.generate_password_hash, 'foo',
                          'bar')

        password = 'foo'
        hashval = security.generate_password_hash(password, 'sha1')
        self.assertTrue(security.check_password_hash(password, hashval))

        hashval = security.generate_password_hash(password, 'sha1',
                                                  pepper='bar')
        self.assertTrue(security.check_password_hash(password, hashval,
                                                     pepper='bar'))

        hashval = security.generate_password_hash(password, 'md5')
        self.assertTrue(security.check_password_hash(password, hashval))

        hashval = security.generate_password_hash(password, 'plain')
        v = security.check_password_hash(password, hashval)
        self.assertTrue(v)

        hashval = security.generate_password_hash(password, 'plain')
        self.assertFalse(security.check_password_hash(password, ''))

        hashval1 = security.hash_password(
            six.text_type(password), 'sha1', u'bar')
        hashval2 = security.hash_password(
            six.text_type(password), 'sha1', u'bar')
        self.assertTrue(hashval1 is not None)
        self.assertEqual(hashval1, hashval2)

        hashval1 = security.hash_password(six.text_type(password), 'md5', None)
        hashval2 = security.hash_password(six.text_type(password), 'md5', None)
        self.assertTrue(hashval1 is not None)
        self.assertEqual(hashval1, hashval2)


if __name__ == '__main__':
    unittest.main()
