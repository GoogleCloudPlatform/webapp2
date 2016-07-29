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

import test_base

from webapp2_extras import securecookie


class TestSecureCookie(test_base.BaseTestCase):
    def test_secure_cookie_serializer(self):
        serializer = securecookie.SecureCookieSerializer('secret-key')
        serializer._get_timestamp = lambda: 1

        value = ['a', 'b', 'c']
        result = "WyJhIiwiYiIsImMiXQ==|1|38" \
                 "837d6af8ac1ded9292b83924fc8521ce76f47e"

        rv = serializer.serialize('foo', value)
        self.assertEqual(rv, result)

        rv = serializer.deserialize('foo', result)
        self.assertEqual(rv, value)

        # no value
        rv = serializer.deserialize('foo', None)
        self.assertEqual(rv, None)

        # not 3 parts
        rv = serializer.deserialize('foo', 'a|b')
        self.assertEqual(rv, None)

        # bad signature
        rv = serializer.deserialize('foo', result + 'foo')
        self.assertEqual(rv, None)

        # too old
        rv = serializer.deserialize('foo', result, max_age=-86400)
        self.assertEqual(rv, None)

        # not correctly encoded
        serializer2 = securecookie.SecureCookieSerializer('foo')
        serializer2._encode = lambda x: 'foo'
        result2 = serializer2.serialize('foo', value)
        rv2 = serializer2.deserialize('foo', result2)
        self.assertEqual(rv2, None)


if __name__ == '__main__':
    test_base.main()
