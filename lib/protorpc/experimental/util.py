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

"""Experimental utils.

These utility classes should be considered very unstable.  They might change
and move around unexpectedly.  Use at your own risk.
"""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import logging
import re
import wsgiref
from wsgiref import util as wsgiref_util

from protorpc import remote
from protorpc import util

__all__ = [
  'Error',
  'ServiceConfigurationError',

  'ProtocolConfig',
  'Protocols',
]


class Error(Exception):
  """Base class for all errors in service handlers module."""


class ServiceConfigurationError(Error):
  """When service configuration is incorrect."""


class ProtocolConfig(object):
  """Configuration for single protocol mapping.

  A read-only protocol configuration provides a given protocol implementation
  with a name and a set of content-types that it recognizes.

  Properties:
    protocol: The protocol implementation for configuration (for example,
      protojson, protobuf, etc.).
    name: Name of protocol configuration.
    default_content_type: The default content type for the protocol.
    alternative_content_types: A list of alternative content-types supported
      by the protocol.  Must not contain the default content-type, nor
      duplicates.
    content_types: A list of all content-types supported by configuration.
      Combination of default content-type and alternatives.
  """

  def __init__(self,
               protocol,
               name,
               default_content_type=None,
               alternative_content_types=None):
    """Constructor.

    Args:
      protocol: The protocol implementation for configuration.
      name: The name of the protocol configuration.
      default_content_type: The default content-type for protocol.  If none
        provided it will check protocol.CONTENT_TYPE.
      alternative_content_types:  A list of content-types.

    Raises:
      ServiceConfigurationError if there are any duplicate content-types.
    """
    self.__protocol = protocol
    self.__name = name
    self.__default_content_type = default_content_type or protocol.CONTENT_TYPE
    self.__alternative_content_types = tuple(alternative_content_types or [])
    self.__content_types = (
      (self.__default_content_type,) + self.__alternative_content_types)
    previous_type = object()
    for content_type in sorted(self.content_types):
      if content_type == previous_type:
        raise ServiceConfigurationError(
          'Duplicate content-type %s' % content_type)
      previous_type = content_type

  @property
  def protocol(self):
    return self.__protocol

  @property
  def name(self):
    return self.__name

  @property
  def default_content_type(self):
    return self.__default_content_type

  @property
  def alternate_content_types(self):
    return self.__alternative_content_types

  @property
  def content_types(self):
    return self.__content_types      


class Protocols(object):
  """Collection of protocol configurations.

  Used to describe a complete set of content-type mappings for multiple
  protocol configurations.

  Properties:
    names: Sorted list of the names of registered protocols.
    content_types: Sorted list of supported content-types.
  """

  def __init__(self):
    """Constructor."""
    self.__by_name = {}
    self.__by_content_type = {}

  def add_protocol_config(self, config):
    """Add a protocol configuration to protocol mapping.

    Args:
      config: A ProtocolConfig.

    Raises:
      ServiceConfigurationError if protocol.name is already registered
        or any of it's content-types are already registered.
    """
    if config.name in self.__by_name:
      raise ServiceConfigurationError(
        'Protocol name %r is already in use' % config.name)
    for content_type in config.content_types:
      if content_type in self.__by_content_type:
        raise ServiceConfigurationError(
          'Content type %r is already in use' % content_type)

    self.__by_name[config.name] = config
    self.__by_content_type.update((t, config) for t in config.content_types)

  def add_protocol(self, *args, **kwargs):
    """Add a protocol configuration from basic parameters.

    Simple helper method that creates and registeres a ProtocolConfig instance.
    """
    self.add_protocol_config(ProtocolConfig(*args, **kwargs))

  @property
  def names(self):
    return tuple(sorted(self.__by_name))

  @property
  def content_types(self):
    return tuple(sorted(self.__by_content_type))

  def lookup_by_name(self, name):
    """Look up a ProtocolConfig by name.

    Args:
      name: Name of protocol to look for.

    Returns:
      ProtocolConfig associated with name.

    Raises:
      KeyError if there is no protocol for name.
    """
    return self.__by_name[name]

  def lookup_by_content_type(self, content_type):
    """Look up a ProtocolConfig by content-type.

    Args:
      content_type: Content-type to find protocol configuration for.

    Returns:
      ProtocolConfig associated with content-type.

    Raises:
      KeyError if there is no protocol for content-type.
    """
    return self.__by_content_type[content_type]
