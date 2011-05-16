#!/usr/bin/env python
#
# Copyright 2010 Google Inc.
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

"""Tests for protorpc.dynamic."""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import unittest

from protorpc import dynamic
from protorpc import test_util
from google.protobuf import descriptor


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):

  MODULE = dynamic


class Color(dynamic.Enum):
  RED = 1
  GREEN = 2L
  BLUE = 4


class EnumTest(test_util.TestCase):
  """Tests for Enum class."""

  def testDefinition(self):
    """Test correct Enum definition."""
    self.assertEquals(1, Color.RED)
    self.assertEquals(2, Color.GREEN)
    self.assertEquals(4, Color.BLUE)

    self.assertEquals([('RED', 1),
                       ('GREEN', 2),
                       ('BLUE', 4)],
                      Color._VALUES)

  def testIntegerOnly(self):
    """Test that only integers are permitted values for class."""
    def do_test():
      class Stuff(dynamic.Enum):

        A_STRING = 'a string'

    self.assertRaises(dynamic.EnumDefinitionError, do_test)

  def testNoEnumSubclass(self):
    """Test that it is not possible to sub-class Enum types."""
    def do_test():
      class MoreColor(Color):

        MAGENTA = 4

    self.assertRaises(dynamic.EnumDefinitionError, do_test)

  def testNoConstructor(self):
    """Test that it is not possible to construct Enum values."""
    self.assertRaises(NotImplementedError, Color)


class MessageTest(test_util.TestCase):
  """Tests for Message class."""

  def testEmptyDefinition(self):
    """Test the creation of an empty message definition."""
    class MyMessage(dynamic.Message):
      pass

    self.assertEquals([], MyMessage.DESCRIPTOR.enum_types)
    self.assertEquals([], MyMessage.DESCRIPTOR.nested_types)
    self.assertEquals([], MyMessage.DESCRIPTOR.fields)

    self.assertEquals('MyMessage', MyMessage.DESCRIPTOR.name)
    self.assertEquals('__main__.MyMessage', MyMessage.DESCRIPTOR.full_name)

  def testNestedDefinition(self):
    """Test nesting message definitions in another."""
    class MyMessage(dynamic.Message):

      class NestedMessage(dynamic.Message):

        pass

    self.assertEquals('NestedMessage', MyMessage.NestedMessage.DESCRIPTOR.name)
    self.assertEquals('__main__.MyMessage.NestedMessage',
                      MyMessage.NestedMessage.DESCRIPTOR.full_name)
    self.assertEquals(MyMessage.DESCRIPTOR,
                      MyMessage.NestedMessage.DESCRIPTOR.containing_type)
    self.assertEquals([MyMessage.NestedMessage.DESCRIPTOR],
                      MyMessage.DESCRIPTOR.nested_types)

  def testNestedEnum(self):
    """Test nesting an Enum type within a definition."""
    class MyMessage(dynamic.Message):

      class Greek(dynamic.Enum):
        ALPHA = 1
        BETA = 2
        GAMMA = 4

    self.assertFalse(hasattr(MyMessage, 'Greek'))
    self.assertEquals(1, len(MyMessage.DESCRIPTOR.enum_types))

    Greek = MyMessage.DESCRIPTOR.enum_types[0]
    self.assertEquals('Greek', Greek.name)
    self.assertEquals('__main__.MyMessage.Greek', Greek.full_name)
    self.assertEquals(MyMessage.DESCRIPTOR, Greek.containing_type)

    self.assertEquals(3, len(Greek.values))
    ALPHA = Greek.values[0]
    BETA = Greek.values[1]
    GAMMA = Greek.values[2]

    self.assertEquals(Greek, ALPHA.type)
    self.assertEquals(Greek, BETA.type)
    self.assertEquals(Greek, GAMMA.type)

    self.assertEquals(1, MyMessage.ALPHA)
    self.assertEquals(2, MyMessage.BETA)
    self.assertEquals(4, MyMessage.GAMMA)

  def testOptionalFields(self):
    """Test optional fields."""
    class MyMessage(dynamic.Message):

      f1 = dynamic.IntegerField(1)
      f2 = dynamic.StringField(2)

    m1 = MyMessage()
    self.assertTrue(m1.IsInitialized())
    m1.f1 = 102
    self.assertTrue(m1.IsInitialized())
    m1.f2 = 'a string'
    self.assertTrue(m1.IsInitialized())

  def testRequiredFields(self):
    """Test required fields."""
    class MyMessage(dynamic.Message):

      f1 = dynamic.IntegerField(1, required=True)
      f2 = dynamic.StringField(2, required=True)

    m1 = MyMessage()
    self.assertFalse(m1.IsInitialized())
    m1.f1 = 102
    self.assertFalse(m1.IsInitialized())
    m1.f2 = 'a string'
    self.assertTrue(m1.IsInitialized())

  def testRepeatedFields(self):
    """Test repeated fields."""
    class MyMessage(dynamic.Message):

      f1 = dynamic.IntegerField(1, repeated=True)
      f2 = dynamic.StringField(2, repeated=True)

    m1 = MyMessage()
    self.assertTrue(m1.IsInitialized())
    m1.f1.append(102)
    self.assertTrue(m1.IsInitialized())
    m1.f2.append('a string')
    self.assertTrue(m1.IsInitialized())

  def testFieldDescriptor(self):
    """Test field descriptors after message class creation."""
    class MyMessage(dynamic.Message):

      f1 = dynamic.IntegerField(1)

      class Nested(dynamic.Message):

        f2 = dynamic.IntegerField(1)

    self.assertEquals(1, len(MyMessage.DESCRIPTOR.fields))
    self.assertEquals(1, len(MyMessage.Nested.DESCRIPTOR.fields))

    f1 = MyMessage.DESCRIPTOR.fields[0]
    self.assertEquals('f1', f1.name)
    self.assertEquals('__main__.MyMessage.f1', f1.full_name)
    self.assertEquals(MyMessage.DESCRIPTOR, f1.containing_type)

    f2 = MyMessage.Nested.DESCRIPTOR.fields[0]
    self.assertEquals('f2', f2.name)
    self.assertEquals('__main__.MyMessage.Nested.f2', f2.full_name)
    self.assertEquals(MyMessage.Nested.DESCRIPTOR, f2.containing_type)

  def testRequiredAndRepeated(self):
    """Test using required and repeated flags together."""
    def do_test():
      class MyMessage(dynamic.Message):

        f1 = dynamic.IntegerField(1, required=True, repeated=True)

    self.assertRaises(dynamic.MessageDefinitionError, do_test)

  def testDefaults(self):
    """Test using default values."""
    class MyMessage(dynamic.Message):

      f1 = dynamic.IntegerField(1, default=10)

    m = MyMessage()

    self.assertEquals(10, m.f1)

  def testNoDefaultList(self):
    """Test that default does not work for repeated fields."""
    def do_test():
      class MyMessage(dynamic.Message):

        f1 = dynamic.IntegerField(1, repeated=True, default=[1, 2, 3])

    self.assertRaises(dynamic.MessageDefinitionError, do_test)

  def testUnexpectedFieldArgument(self):
    """Test that unknown keyword arguments may not be used."""
    self.assertRaises(TypeError, dynamic.IntegerField, 1, whatever=10)

  def testOverrideVariant(self):
    """Test overriding the variant of a field."""
    class MyMessage(dynamic.Message):

      f1 = dynamic.IntegerField(1)
      f2 = dynamic.IntegerField(2,
                                variant=descriptor.FieldDescriptor.TYPE_UINT32)

    self.assertEquals(descriptor.FieldDescriptor.TYPE_INT64,
                      MyMessage.DESCRIPTOR.fields[0].type)
    self.assertEquals(descriptor.FieldDescriptor.TYPE_UINT32,
                      MyMessage.DESCRIPTOR.fields[1].type)

  def testOverrideWrongVariant(self):
    """Test assigning an incompatible variant."""
    def do_test():
      class MyMessage(dynamic.Message):

        f1 = dynamic.IntegerField(
            1, variant=descriptor.FieldDescriptor.TYPE_STRING)

    self.assertRaises(dynamic.MessageDefinitionError, do_test)

  def testDoNotAllowNonDefinitionValues(self):
    """Test that non-definitions may not be assigned to class."""
    def do_test():
      class MyMessage(dynamic.Message):

        f1 = 'A non-field value.'

    self.assertRaises(dynamic.MessageDefinitionError, do_test)

  def testDoNotAllowMethods(self):
    """Test that methods may not be defined on class."""
    def do_test():
      class MyMessage(dynamic.Message):

        def i_dont_think_so(self):
          pass

    self.assertRaises(dynamic.MessageDefinitionError, do_test)

  def testDoNotSubclassing(self):
    """Test that messages may not be sub-classed."""
    class MyMessage(dynamic.Message):

      pass

    def do_test():
      class SubClass(MyMessage):

        pass

    self.assertRaises(dynamic.MessageDefinitionError, do_test)

  def testEnumField(self):
    """Test a basic enum field."""
    class MyMessage(dynamic.Message):

      class Color(dynamic.Enum):
        RED = 1
        GREEN = 2
        BLUE = 3

      color = dynamic.EnumField(Color, 1)

    self.assertEquals(1, len(MyMessage.DESCRIPTOR.fields))

    color = MyMessage.DESCRIPTOR.fields[0]
    self.assertEquals('color', color.name)
    self.assertEquals('__main__.MyMessage.color', color.full_name)

    Color = color.enum_type
    self.assertEquals(MyMessage.DESCRIPTOR.enum_types[0], Color)

  def testEnumFieldWithNonEnum(self):
    """Test enum field with a non-enum class."""
    def do_test():
      class MyMessage(dynamic.Message):

        class Color(object):

          RED = 1
          GREEN = 2
          BLUE = 3

        color = dynamic.EnumField(Color, 1)

    self.assertRaises(TypeError, do_test)

  def testEnumFieldWithNonNestedEnum(self):
    """Test enum field with a non-peer Enum class."""
    class Color(dynamic.Enum):

      RED = 1
      GREEN = 2
      BLUE = 3

    def do_test():
      class MyMessage(dynamic.Message):

        color = dynamic.EnumField(Color, 1)

    self.assertRaises(dynamic.MessageDefinitionError, do_test)

  def testNoAbitraryAssignment(self):
    """Test that not possible to assing non-field attributes."""
    class MyMessage(dynamic.Message):

      pass

    self.assertRaises(AttributeError, setattr, MyMessage(), 'a', 10)


if __name__ == '__main__':
  unittest.main()
