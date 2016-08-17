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

from webapp2_extras import json


class TestJson(unittest.TestCase):
    def test_encode(self):
        self.assertEqual(json.encode(
            '<script>alert("hello")</script>'),
            '"<script>alert(\\"hello\\")<\\/script>"')

    def test_decode(self):
        self.assertEqual(json.decode(
            '"<script>alert(\\"hello\\")<\\/script>"'),
            '<script>alert("hello")</script>')

    def test_b64encode(self):
        self.assertEqual(json.b64encode(
            '<script>alert("hello")</script>'),
            b'IjxzY3JpcHQ+YWxlcnQoXCJoZWxsb1wiKTxcL3NjcmlwdD4i')

    def test_b64decode(self):
        self.assertEqual(json.b64decode(
            'IjxzY3JpcHQ+YWxlcnQoXCJoZWxsb1wiKTxcL3NjcmlwdD4i'),
            '<script>alert("hello")</script>')

    def test_quote(self):
        self.assertEqual(
            json.quote('<script>alert("hello")</script>'),
            '%22%3Cscript%3Ealert%28%5C%22hello%5C%22%29%3C%5C/script%3E%22'
        )

    def test_unquote(self):
        self.assertEqual(json.unquote(
            '%22%3Cscript%3Ealert%28%5C%22hello%5C%22%29%3C%5C/script%3E%22'
        ),
            '<script>alert("hello")</script>'
        )


if __name__ == '__main__':
    unittest.main()
