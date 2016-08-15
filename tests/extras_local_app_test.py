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

import webapp2
from webapp2_extras import local_app


class TestLocalApp(unittest.TestCase):
    def test_dispatch(self):
        def hello_handler(request, *args, **kwargs):
            return webapp2.Response('Hello, World!')

        app = local_app.WSGIApplication([('/', hello_handler)])
        rsp = app.get_response('/')
        self.assertEqual(rsp.status_int, 200)
        self.assertEqual(rsp.body, 'Hello, World!')


if __name__ == '__main__':
    unittest.main()
