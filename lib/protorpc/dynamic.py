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

"""Library for defining protocol messages in the Python language."""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import itertools

from google.protobuf import descriptor
from google.protobuf import message
from google.protobuf import reflection

from protorpc import util


__all__ = ['Error',
           'EnumDefinitionError',
           'MessageDefinitionError',

           'BooleanField',
           'BytesField',
           'Enum',
           'EnumField',
           'FloatField',
           'IntegerField',
           'Message',
           'StringField',
]


class Error(Exception):
  """Base class for message exceptions."""


class EnumDefinitionError(Error):
  """Enumeration definition error."""


class MessageDefinitionError(Error):
  """Message definition error."""


_CPP_TYPE_MAP = {
  descriptor.FieldDescriptor.TYPE_DOUBLE:
      descriptor.FieldDescriptor.CPPTYPE_DOUBLE,
  descriptor.FieldDescriptor.TYPE_FLOAT:
      descriptor.FieldDescriptor.CPPTYPE_FLOAT,
  descriptor.FieldDescriptor.TYPE_INT64:
      descriptor.FieldDescriptor.CPPTYPE_INT64,
  descriptor.FieldDescriptor.TYPE_UINT64:
      descriptor.FieldDescriptor.CPPTYPE_UINT64,
  descriptor.FieldDescriptor.TYPE_INT32:
      descriptor.FieldDescriptor.CPPTYPE_INT32,
  descriptor.FieldDescriptor.TYPE_FIXED64:
      descriptor.FieldDescriptor.CPPTYPE_DOUBLE,
  descriptor.FieldDescriptor.TYPE_FIXED32:
      descriptor.FieldDescriptor.CPPTYPE_DOUBLE,
  descriptor.FieldDescriptor.TYPE_BOOL:
      descriptor.FieldDescriptor.CPPTYPE_BOOL,
  descriptor.FieldDescriptor.TYPE_STRING:
      descriptor.FieldDescriptor.CPPTYPE_STRING,
  descriptor.FieldDescriptor.TYPE_MESSAGE:
      descriptor.FieldDescriptor.CPPTYPE_MESSAGE,
  descriptor.FieldDescriptor.TYPE_BYTES:
      descriptor.FieldDescriptor.CPPTYPE_STRING,
  descriptor.FieldDescriptor.TYPE_UINT32:
      descriptor.FieldDescriptor.CPPTYPE_UINT32,
  descriptor.FieldDescriptor.TYPE_ENUM:
      descriptor.FieldDescriptor.CPPTYPE_ENUM,
  descriptor.FieldDescriptor.TYPE_SFIXED32:
      descriptor.FieldDescriptor.CPPTYPE_INT32,
  descriptor.FieldDescriptor.TYPE_SFIXED64:
      descriptor.FieldDescriptor.CPPTYPE_INT64,
  descriptor.FieldDescriptor.TYPE_SINT32:
      descriptor.FieldDescriptor.CPPTYPE_INT32,
  descriptor.FieldDescriptor.TYPE_SINT64:
      descriptor.FieldDescriptor.CPPTYPE_INT64,
}


class _EnumType(type):
  """Meta-class used for defining the Enum classes.

  Meta-class enables very specific behavior for any defined Enum
  class.  All attributes defined on an Enum sub-class must be non-repeating
  integers. The meta-class ensures that only one level of Enum class hierarchy
  is possible.  In other words it is not possible to delcare sub-classes
  of sub-classes of Enum.

  The class definition is used mainly for syntactic sugar.  It is used by the
  _DynamicProtocolMessageType meta-class to initialize a descriptor object and
  then discarded.  The class definition will NOT appear in the resulting class.

  The meta-class creates a class attribute _VALUES which is an ordered list of
  tuples (name, number) of the Enum definition in number order.
  """

  __initialized = False

  __allowed_names = None

  def __new__(cls, name, bases, dictionary):
    if not _EnumType.__initialized:
      _EnumType.__initialized = True
    else:
      if bases != (Enum,):
        raise EnumDefinitionError('Enum classes may not be subclassed.')

      if not _EnumType.__allowed_names:
        _EnumType.__allowed_names = set(dir(Enum))

      values = []
      for attribute_name, value in dictionary.iteritems():
        if attribute_name == '__module__':
          continue
        if not isinstance(value, (int, long)):
          raise EnumDefinitionError('Enum value %s must be an integer.' % value)
        values.append((attribute_name, value))
      values.sort(key=lambda v: v[1])
      dictionary['_VALUES'] = values

    return super(_EnumType, cls).__new__(cls, name, bases, dictionary)


class Enum(object):
  """Base class for all enumerated types.

  Enumerated types are not meant to be instantiated.
  """

  __metaclass__ = _EnumType

  def __init__(self):
    raise NotImplementedError()


class _DynamicProtocolMessageType(reflection.GeneratedProtocolMessageType):
  """Meta-class used for defining the dynamic Message base class.

  For more details about Message classes, see the Message class docstring
  and protocol buffers:

    http://code.google.com/apis/protocolbuffers/docs/reference/python/index.html

  This meta-class enables very specific behavior for any defined Message
  class.  All attributes defined on an Message sub-class must be field
  instances, Enum class definitions or other Message class definitions.  Each
  field attribute defined on an Message sub-class is added to the set of
  field definitions and the attribute is translated in to FieldDescriptor.  It
  also ensures that only one level of Message class hierarchy is possible.  In
  other words it is not possible to declare sub-classes of sub-classes of
  Message.
  """

  def __new__(cls, name, bases, dictionary):
    enums = []
    enum_map = {}
    messages = []
    field_definitions = []
    fields = []
    module = dictionary['__module__']

    def update_nested_definitions(definition, root_name):
      """Update nested message, enum and field definitions

      When each message class is created, it cannot know what it's containing
      parent is.  It is therefore necessary to recreate the full-name of nested
      messagse, enums and fields when every new message is created and to
      assign the definition's containing type.

      This method is recursive because any message definitions found within
      must also be updated.

      Args:
        definition: Definition that will be updated.
        root_name: The name of the module or definition containing this
          definition.
      """
      # TODO(rafek): This is potentially an expensive process.  Ideally the
      # descriptor should be able to generate a full name for a class based
      # on the containing types.
      definition.full_name = '%s.%s' % (root_name, definition.name)
      if isinstance(definition, descriptor.Descriptor):
        for sub_definition in itertools.chain(definition.nested_types,
                                              definition.enum_types,
                                              definition.fields):
          update_nested_definitions(sub_definition, definition.full_name)
          sub_definition.containing_type = definition

    # No additional intialization necessary for Message class defined in this
    # module.
    if bases != (message.Message,):

      # Do not subclass message classes.
      if bases != (Message,):
        raise MessageDefinitionError('May not subclass Message types.')

      # Configure nested definitions and fields.
      for attribute_name, value in dictionary.iteritems():
        if attribute_name == '__module__':
          continue

        # Enumeration definitions.
        if isinstance(value, type) and issubclass(value, Enum):
          enum_numbers = []
          for index, (enum_name, enum_number) in enumerate(value._VALUES):
            enum_numbers.append(descriptor.EnumValueDescriptor(name=enum_name,
                                                            index=index,
                                                            number=enum_number))
          enum = descriptor.EnumDescriptor(name=attribute_name,
                                           full_name='',
                                           filename='',
                                           values=enum_numbers)
          enums.append(enum)
          enum_map[enum.name] = enum

        # Sub-message defintions.
        elif isinstance(value, type) and issubclass(value, message.Message):
          messages.append(value.DESCRIPTOR)

        # Field definitions.  The fields are not configured here since they
        # must be processed in numeric order.
        elif isinstance(value, _Field):
          field_definitions.append((attribute_name, value))

        else:
          raise MessageDefinitionError('Non-definition field %s.'
                                       % attribute_name)

      # Define fields in numeric order.
      field_definitions.sort(key=lambda v: v[1].number)
      for index, (attribute_name, field) in enumerate(field_definitions):
        if field.required and field.repeated:
          raise MessageDefinitionError('Field %s must be either required '
                                       'or repeated, not both' % attribute_name)

        default_value = field.default
        if field.required:
          label = descriptor.FieldDescriptor.LABEL_REQUIRED
        elif field.repeated:
          label = descriptor.FieldDescriptor.LABEL_REPEATED
          if default_value is None:
            default_value = []
        else:
          label = descriptor.FieldDescriptor.LABEL_OPTIONAL

        if isinstance(field, EnumField):
          try:
            enum_type = enum_map[field.enum_type.__name__]
          except KeyError:
            raise MessageDefinitionError('Field %s may only use Enum type '
                                         'defined in same Message.'
                                         % attribute_name)
        else:
          enum_type = None

        fields.append(descriptor.FieldDescriptor(
            name=attribute_name,
            full_name='',
            index=index,
            number=field.number,
            type=field.variant,
            cpp_type=_CPP_TYPE_MAP[field.variant],
            label=label,
            default_value=default_value,
            message_type=None,
            enum_type=enum_type,
            containing_type=None,
            is_extension=False,
            extension_scope=None,
            has_default_value=field.default is not None))

      # Throw away the Enum class definitions.
      for enum in enums:
        del dictionary[enum.name]

    # Define message descriptor.
    message_descriptor = descriptor.Descriptor(name=name,
                                               full_name='',
                                               filename='',
                                               containing_type=None,
                                               fields=fields,
                                               nested_types=messages,
                                               enum_types=enums,
                                               extensions=[])
    update_nested_definitions(message_descriptor, module)
    dictionary[_DynamicProtocolMessageType._DESCRIPTOR_KEY] = message_descriptor

    if bases == (message.Message,):
      superclass = super(reflection.GeneratedProtocolMessageType, cls)
    else:
      superclass = super(_DynamicProtocolMessageType, cls)
    return superclass.__new__(cls, name, bases, dictionary)


class Message(message.Message):
  """Base class for user defined message objects.

  Used to define messages for efficient transmission across network or
  process space.  Messages are defined using the field classes (IntegerField,
  FloatField, EnumField, etc.).

  Messages are more restricted than normal classes in that they may only
  contain field attributes and other Message and Enum definitions.  These
  restrictions are in place because the structure of the Message class is
  intentended to itself be transmitted across network or process space and
  used directly by clients or even other servers.  As such methods and
  non-field attributes could not be transmitted with the structural information
  causing discrepancies between different languages and implementations.

  For more detail about how this message class works, please see:

    http://code.google.com/apis/protocolbuffers/docs/reference/python/index.html

  Field definitions are discarded by the meta-class and do not appear in the
  final class definition.  In their place are a property instance defined by
  reflection.GeneratedProtocolMessageType.

  Example:

    class Lot(Message):
      price = IntegerField(1, required=True)
      quantity = IntegerField(2, required=True)

    class Order(Message):
      class TradeType(Enum):
        BUY = 1
        SELL = 2
        SHORT = 3
        CALL = 4

      symbol = StringProperty(1, required=True)
      total_quantity = IntegerProperty(2, required=True)
      trade_type = EnumProperty(TradeType, 3, required=True)
      limit = IntegerField(5)

    order = Order()

    assert not order.IsInitialized()

    order.symbol = 'GOOG'
    order.total_quantity = 10
    order.trade_type = Order.BUY

    # Now object is initialized!
    assert order.IsInitialized()
  """

  __metaclass__ = _DynamicProtocolMessageType

  __slots__ = []


class _Field(object):

  @util.positional(2)
  def __init__(self,
               number,
               required=False,
               repeated=False,
               variant=None,
               default=None):
    """Constructor.

    Store the attributes of a field so that the _DynamicProtocolMessageType
    meta-class can use it to populate field descriptors for the Message
    class.  Instances of field are discarded after used by the meta-class.

    The required and repeated parameters are mutually exclusive.  Setting both
    to True will raise a FieldDefinitionError.

    Repeated fields may not have default values.

    Sub-class Attributes:
      Each sub-class of _Field must define the following:
        VARIANTS: Set of variant types accepted by that field.
        DEFAULT_VARIANT: Default variant type if not specified in constructor.

    Args:
      number: Number of field.  Must be unique per message class.
      required: Whether or not field is required.  Mutually exclusive with
        'repeated'.
      repeated: Whether or not field is repeated.  Mutually exclusive with
        'required'.
      variant: Wire-format variant hint.
      default: Default value for field if not found in stream.

    Raises:
      MessageDefinitionError when repeated fields are provided a default value
        or when an incompatible variant is provided.
      TypeError when an unexpected keyword argument is provided.
    """
    self.number = number
    self.required = required
    self.repeated = repeated

    if self.repeated and default is not None:
      raise MessageDefinitionError(
          'May not provide default for repeated fields.')
    self.default = default

    if variant is None:
      self.variant = self.DEFAULT_VARIANT
    else:
      self.variant = variant

    if self.variant not in self.VARIANTS:
      raise MessageDefinitionError('Bad variant.')


class IntegerField(_Field):
  """Field definition for integer values."""

  DEFAULT_VARIANT = descriptor.FieldDescriptor.TYPE_INT64

  VARIANTS = frozenset([descriptor.FieldDescriptor.TYPE_INT32,
                        descriptor.FieldDescriptor.TYPE_INT64,
                        descriptor.FieldDescriptor.TYPE_UINT32,
                        descriptor.FieldDescriptor.TYPE_INT64,
                        descriptor.FieldDescriptor.TYPE_SINT32,
                        descriptor.FieldDescriptor.TYPE_SINT64,
                       ])


class FloatField(_Field):
  """Field definition for float values."""

  DEFAULT_VARIANT = descriptor.FieldDescriptor.TYPE_DOUBLE

  VARIANTS = frozenset([descriptor.FieldDescriptor.TYPE_FLOAT,
                        descriptor.FieldDescriptor.TYPE_DOUBLE,
                       ])


class BooleanField(_Field):
  """Field definition for boolean values."""

  DEFAULT_VARIANT = descriptor.FieldDescriptor.TYPE_BOOL

  VARIANTS = frozenset([descriptor.FieldDescriptor.TYPE_BOOL])


class BytesField(_Field):
  """Field definition for byte (str) values."""

  DEFAULT_VARIANT = descriptor.FieldDescriptor.TYPE_BYTES

  VARIANTS = frozenset([descriptor.FieldDescriptor.TYPE_BYTES])


class StringField(_Field):
  """Field definition for unicode string values."""

  DEFAULT_VARIANT = descriptor.FieldDescriptor.TYPE_STRING

  VARIANTS = frozenset([descriptor.FieldDescriptor.TYPE_STRING])


class EnumField(_Field):
  """Field definition for enum values."""

  DEFAULT_VARIANT = descriptor.FieldDescriptor.TYPE_ENUM

  VARIANTS = frozenset([descriptor.FieldDescriptor.TYPE_ENUM])

  def __init__(self, enum_type, number, **kwargs):
    """Constructor.

    Args:
      enum_type: Enum type for field.  Must be subclass of Enum.
      number: Number of field.  Must be unique per message class.
      required: Whether or not field is required.  Mutually exclusive to
        'repeated'.
      repeated: Whether or not field is repeated.  Mutually exclusive to
        'required'.
      default: Default value for field if not found in stream.

    Raises:
      TypeError when invalid enum_type is provided.
    """
    # TODO(rafek): Support enumerated types outside of single message
    # definition scope.
    if isinstance(enum_type, type) and not issubclass(enum_type, Enum):
      raise TypeError('Enum field requires Enum class.')

    self.enum_type = enum_type
    super(EnumField, self).__init__(number, **kwargs)
