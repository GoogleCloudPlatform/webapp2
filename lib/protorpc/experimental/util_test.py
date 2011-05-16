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

"""Tests for protorpc.experimental.util."""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import unittest

from protorpc.experimental import util
from protorpc import protojson
from protorpc import test_util

package = 'testpackage'


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):

  MODULE = util


# TODO(rafek): Test case insensitive.
class ProtocolConfigTest(test_util.TestCase):

  def testConstructor(self):
    config = util.ProtocolConfig(
      protojson,
      'proto1',
      'application/x-json',
      iter(['text/json', 'text/javascript']))
    self.assertEquals(protojson, config.protocol)
    self.assertEquals('proto1', config.name)
    self.assertEquals('application/x-json', config.default_content_type)
    self.assertEquals(('text/json', 'text/javascript'),
                      config.alternate_content_types)
    self.assertEquals(('application/x-json', 'text/json', 'text/javascript'),
                      config.content_types)

  def testConstructorDefaults(self):
    config = util.ProtocolConfig(
      protojson,
      'proto2')
    self.assertEquals(protojson, config.protocol)
    self.assertEquals('proto2', config.name)
    self.assertEquals('application/json', config.default_content_type)
    self.assertEquals((), config.alternate_content_types)
    self.assertEquals(('application/json',), config.content_types)

  def testDuplicateContentTypes(self):
    self.assertRaises(util.ServiceConfigurationError,
                      util.ProtocolConfig,
                      protojson,
                      'json',
                      'text/plain',
                      ('text/plain',))
    self.assertRaises(util.ServiceConfigurationError,
                      util.ProtocolConfig,
                      protojson,
                      'json',
                      'text/plain',
                      ('text/html', 'text/html'))


# TODO(rafek): Test case insensitive.
# TODO(rafek): Test lookup functions.
class ProtocolsTest(test_util.TestCase):

  def setUp(self):
    self.protocols = util.Protocols()

  def testEmpty(self):
    self.assertEquals((), self.protocols.names)
    self.assertEquals((), self.protocols.content_types)

  def testHasConfigs(self):
    self.protocols.add_protocol(protojson, 'json')
    self.protocols.add_protocol(protojson, 'json2', 'text/x-json')
    self.protocols.add_protocol(
      protojson, 'alpha', 'text/plain', ('text/other',))
    self.assertEquals(('alpha', 'json', 'json2'), self.protocols.names)
    self.assertEquals(('application/json',
                       'text/other',
                       'text/plain',
                       'text/x-json'),
                      self.protocols.content_types)


def main():
  unittest.main()


if __name__ == '__main__':
  main()
