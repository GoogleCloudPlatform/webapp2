#!/usr/bin/env python
#
# Copyright 2011 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""End to end tests for ProtoRPC."""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import logging
import unittest

from google.appengine.ext import webapp

from protorpc import test_util
from protorpc import webapp_test_util

package = 'test_package'


class EndToEndTest(webapp_test_util.EndToEndTestBase):

  def testSimpleRequest(self):
    self.assertEquals(test_util.OptionalMessage(string_value='+blar'),
                      self.stub.optional_message(string_value='blar'))


def main():
  unittest.main()


if __name__ == '__main__':
  main()
