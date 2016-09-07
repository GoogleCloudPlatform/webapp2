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

import unittest

from webapp2_extras import securecookie


class TestSecureCookie(unittest.TestCase):
    def test_secure_cookie_serializer(self):
        serializer = securecookie.SecureCookieSerializer(b'secret-key')
        serializer._get_timestamp = lambda: 1

        value = ['a', 'b', 'c']
        result = b"WyJhIiwiYiIsImMiXQ==|1|38" \
                 b"837d6af8ac1ded9292b83924fc8521ce76f47e"

        rv = serializer.serialize(b'foo', value)
        self.assertEqual(rv, result)

        rv = serializer.deserialize(b'foo', result)
        self.assertEqual(rv, value)

        # no value
        rv = serializer.deserialize(b'foo', None)
        self.assertEqual(rv, None)

        # not 3 parts
        rv = serializer.deserialize(b'foo', b'a|b')
        self.assertEqual(rv, None)

        # bad signature
        rv = serializer.deserialize(b'foo', result + b'foo')
        self.assertEqual(rv, None)

        # too old
        rv = serializer.deserialize(b'foo', result, max_age=-86400)
        self.assertEqual(rv, None)

        # not correctly encoded
        serializer2 = securecookie.SecureCookieSerializer(b'foo')
        serializer2._encode = lambda x: b'foo'
        result2 = serializer2.serialize(b'foo', value)
        rv2 = serializer2.deserialize(b'foo', result2)
        self.assertEqual(rv2, None)


if __name__ == '__main__':
    unittest.main()
