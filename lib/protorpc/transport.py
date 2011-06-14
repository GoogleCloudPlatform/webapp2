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

"""Transport library for ProtoRPC.

Contains underlying infrastructure used for communicating RPCs over low level
transports such as HTTP.

Includes HTTP transport built over urllib2.
"""

import logging
import sys
import urllib2

from protorpc import messages
from protorpc import protobuf
from protorpc import remote
from protorpc import util

__all__ = [
  'RpcStateError',

  'HttpTransport',
  'Rpc',
  'Transport',
]


class RpcStateError(messages.Error):
  """Raised when trying to put RPC in to an invalid state."""


class Rpc(object):
  """Represents a client side RPC.

  An RPC is created by the transport class and is used with a single RPC.  While
  an RPC is still in process, the response is set to None.  When it is complete
  the response will contain the response message.
  """

  def __init__(self, request):
    """Constructor.

    Args:
      request: Request associated with this RPC.
    """
    self.__request = request
    self.__response = None
    self.__state = remote.RpcState.RUNNING
    self.__error_message = None
    self.__error_name = None

  @property
  def request(self):
    """Request associated with RPC."""
    return self.__request

  @property
  def response(self):
    """Response associated with RPC."""
    return self.__response

  @property
  def state(self):
    return self.__state

  @property
  def error_message(self):
    return self.__error_message

  @property
  def error_name(self):
    return self.__error_name

  def __set_state(self, state, error_message=None, error_name=None):
    if self.__state != remote.RpcState.RUNNING:
      raise RpcStateError(
        'RPC must be in RUNNING state to change to %s' % state)
    if state == remote.RpcState.RUNNING:
      raise RpcStateError('RPC is already in RUNNING state')
    self.__state = state
    self.__error_message = error_message
    self.__error_name = error_name

  def set_response(self, response):
    # TODO: Even more specific type checking.
    if not isinstance(response, messages.Message):
      raise TypeError('Expected Message type, received %r' % (response))

    self.__response = response
    self.__set_state(remote.RpcState.OK)

  def set_status(self, status):
    status.check_initialized()
    self.__set_state(status.state, status.error_message, status.error_name)


class Transport(object):
  """Transport base class.

  Provides basic support for implementing a ProtoRPC transport such as one
  that can send and receive messages over HTTP.

  Implementations override _transport_rpc.  This method receives an encoded
  response as determined by the transports configured protocol.  The transport
  is expected to set the rpc response or raise an exception before termination.

  Asynchronous transports are not supported.
  """

  @util.positional(1)
  def __init__(self, protocol=protobuf):
    """Constructor.

    Args:
      protocol: The protocol implementation.  Must implement encode_message and
        decode_message.
    """
    self.__protocol = protocol

  @property
  def protocol(self):
    """Protocol associated with this transport."""
    return self.__protocol

  def send_rpc(self, remote_info, request):
    """Initiate sending an RPC over the transport.

    Args:
      remote_info: RemoteInfo instance describing remote method.
      request: Request message to send to service.

    Returns:
      An Rpc instance intialized with request and response.
    """
    request.check_initialized()
    encoded_request = self.__protocol.encode_message(request)
    rpc = Rpc(request)

    self._transport_rpc(remote_info, encoded_request, rpc)

    return rpc

  def _transport_rpc(self, remote_info, encoded_request, rpc):
    """Transport RPC method.

    Args:
      remote_info: RemoteInfo instance describing remote method.
      encoded_request: Request message as encoded by transport protocol.
      rpc: Rpc instance associated with a single request.
    """
    raise NotImplementedError()


class HttpTransport(Transport):
  """Transport for communicating with HTTP servers."""

  @util.positional(2)
  def __init__(self, service_url, protocol=protobuf):
    """Constructor.

    Args:
      service_url: URL where the service is located.  All communication via
        the transport will go to this URL.
      protocol: The protocol implementation.  Must implement encode_message and
        decode_message.
    """
    super(HttpTransport, self).__init__(protocol=protocol)
    self.__service_url = service_url

  def __http_error_to_exception(self, http_error):
    error_code = http_error.code
    content_type = http_error.hdrs.get('content-type')
    if content_type == self.protocol.CONTENT_TYPE:
      try:
        rpc_status = self.protocol.decode_message(remote.RpcStatus,
                                                  http_error.read())
      except Exception, decode_err:
        logging.warning(
          'An error occurred trying to parse status: %s\n%s',
          str(decode_err), http_error.msg)
      else:
        # TODO: Move the check_rpc_status to the Rpc.response property.
        # Will raise exception if rpc_status is in an error state.
        remote.check_rpc_status(rpc_status)

  def _transport_rpc(self, remote_info, encoded_request, rpc):
    """HTTP transport rpc method.

    Uses urllib2 as underlying HTTP transport.
    """
    method_url = '%s.%s' % (self.__service_url, remote_info.method.func_name)
    http_request = urllib2.Request(method_url, encoded_request)
    http_request.add_header('content-type', self.protocol.CONTENT_TYPE)

    try:
      http_response = urllib2.urlopen(http_request)
    except urllib2.HTTPError, err:
      self.__http_error_to_exception(err)

      # TODO: Map other types of errors to appropriate exceptions.

      _, _, trace_back = sys.exc_info()
      raise remote.ServerError, (str(err), err), trace_back

    except urllib2.URLError, err:
      _, _, trace_back = sys.exc_info()
      if isinstance(err, basestring):
        error_message = err
      else:
        error_message = err.args[0]
      raise remote.NetworkError, (error_message, err), trace_back

    encoded_response = http_response.read()
    response = self.protocol.decode_message(remote_info.response_type,
                                            encoded_response)
    rpc.set_response(response)
