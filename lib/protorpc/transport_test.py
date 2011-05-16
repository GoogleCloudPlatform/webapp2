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

import StringIO
import types
import unittest
import urllib2

from protorpc import messages
from protorpc import protobuf
from protorpc import protojson
from protorpc import test_util
from protorpc import remote
from protorpc import transport

import mox


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):

  MODULE = transport


class Message(messages.Message):

  value = messages.StringField(1)


class Service(remote.Service):
  
  @remote.method(Message, Message)
  def method(self, request):
    pass


class RpcTest(test_util.TestCase):

  def setUp(self):
    self.request = Message(value=u'request')
    self.response = Message(value=u'response')
    self.status = remote.RpcStatus(state=remote.RpcState.APPLICATION_ERROR,
                                   error_message='an error',
                                   error_name='blam')

    self.rpc = transport.Rpc(self.request)

  def testConstructor(self):

    self.assertEquals(self.request, self.rpc.request)
    self.assertEquals(remote.RpcState.RUNNING, self.rpc.state)
    self.assertEquals(None, self.rpc.response)
    self.assertEquals(None, self.rpc.error_message)
    self.assertEquals(None, self.rpc.error_name)

  def testSetResponse(self):
    self.rpc.set_response(self.response)

    self.assertEquals(self.request, self.rpc.request)
    self.assertEquals(remote.RpcState.OK, self.rpc.state)
    self.assertEquals(self.response, self.rpc.response)
    self.assertEquals(None, self.rpc.error_message)
    self.assertEquals(None, self.rpc.error_name)

  def testSetResponseAlreadySet(self):
    self.rpc.set_response(self.response)

    self.assertRaisesWithRegexpMatch(
      transport.RpcStateError,
      'RPC must be in RUNNING state to change to OK',
      self.rpc.set_response,
      self.response)

  def testSetResponseAlreadyError(self):
    self.rpc.set_status(self.status)

    self.assertRaisesWithRegexpMatch(
      transport.RpcStateError,
      'RPC must be in RUNNING state to change to OK',
      self.rpc.set_response,
      self.response)

  def testSetStatus(self):
    self.rpc.set_status(self.status)

    self.assertEquals(self.request, self.rpc.request)
    self.assertEquals(remote.RpcState.APPLICATION_ERROR, self.rpc.state)
    self.assertEquals(None, self.rpc.response)
    self.assertEquals('an error', self.rpc.error_message)
    self.assertEquals('blam', self.rpc.error_name)

  def testSetStatusAlreadySet(self):
    self.rpc.set_response(self.response)

    self.assertRaisesWithRegexpMatch(
      transport.RpcStateError,
      'RPC must be in RUNNING state to change to OK',
      self.rpc.set_response,
      self.response)

  def testSetNonMessage(self):
    self.assertRaisesWithRegexpMatch(
      TypeError,
      'Expected Message type, received 10',
      self.rpc.set_response,
      10)

  def testSetStatusAlreadyError(self):
    self.rpc.set_status(self.status)

    self.assertRaisesWithRegexpMatch(
      transport.RpcStateError,
      'RPC must be in RUNNING state to change to OK',
      self.rpc.set_response,
      self.response)

  def testSetUninitializedStatus(self):
    self.assertRaises(messages.ValidationError,
                      self.rpc.set_status,
                      remote.RpcStatus())


class TransportTest(test_util.TestCase):

  def do_test(self, protocol, trans):
    request = Message()
    request.value = u'request'

    response = Message()
    response.value = u'response'

    encoded_request = protocol.encode_message(request)
    encoded_response = protocol.encode_message(response)

    self.assertEquals(protocol, trans.protocol)

    received_rpc = [None]
    def transport_rpc(remote, data, rpc):
      received_rpc[0] = rpc
      self.assertEquals(remote, Service.method.remote)
      self.assertEquals(encoded_request, data)
      self.assertTrue(isinstance(rpc, transport.Rpc))
      self.assertEquals(request, rpc.request)
      self.assertEquals(None, rpc.response)
      rpc.set_response(response)
    trans._transport_rpc = transport_rpc

    rpc = trans.send_rpc(Service.method.remote, request)
    self.assertEquals(received_rpc[0], rpc)

  def testDefaultProtocol(self):
    self.do_test(protobuf, transport.Transport())

  def testAlternateProtocol(self):
    self.do_test(protojson, transport.Transport(protocol=protojson))


class HttpTransportTest(test_util.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.mox.StubOutWithMock(urllib2, 'urlopen')

  def tearDown(self):
    self.mox.UnsetStubs()
    self.mox.VerifyAll()

  @remote.method(Message, Message)
  def my_method(self, request):
    self.fail('self.my_method should not be directly invoked.')

  def do_test_send_rpc(self, protocol):
    trans = transport.HttpTransport('http://myserver/myservice',
                                    protocol=protocol)

    request = Message(value=u'The request value')
    encoded_request = protocol.encode_message(request)

    response = Message(value=u'The response value')
    encoded_response = protocol.encode_message(response)

    def verify_request(urllib2_request):
      self.assertEquals('http://myserver/myservice.my_method',
                        urllib2_request.get_full_url())
      self.assertEquals(urllib2_request.get_data(), encoded_request)
      self.assertEquals(protocol.CONTENT_TYPE,
                        urllib2_request.headers['Content-type'])

      return True

    # First call succeeds.
    urllib2.urlopen(mox.Func(verify_request)).AndReturn(
        StringIO.StringIO(encoded_response))

    # Second call raises a normal HTTP error.
    urllib2.urlopen(mox.Func(verify_request)).AndRaise(
        urllib2.HTTPError('http://whatever',
                          500,
                          'a server error',
                          {},
                          StringIO.StringIO('')))

    # Third call raises a 500 error with message.
    status = remote.RpcStatus(state=remote.RpcState.REQUEST_ERROR,
                              error_message='an error')
    urllib2.urlopen(mox.Func(verify_request)).AndRaise(
        urllib2.HTTPError('http://whatever',
                          500,
                          protocol.encode_message(status),
                          {'content-type': protocol.CONTENT_TYPE},
                          StringIO.StringIO('')))

    # Fourth call is not parsable.
    status = remote.RpcStatus(state=remote.RpcState.REQUEST_ERROR,
                              error_message='an error')
    urllib2.urlopen(mox.Func(verify_request)).AndRaise(
        urllib2.HTTPError('http://whatever',
                          500,
                          'a text message is here anyway',
                          {'content-type': protocol.CONTENT_TYPE},
                          StringIO.StringIO('')))

    self.mox.ReplayAll()

    actual_rpc = trans.send_rpc(self.my_method.remote, request)
    self.assertEquals(response, actual_rpc.response)

    try:
      trans.send_rpc(self.my_method.remote, request)
    except remote.ServerError, err:
      self.assertEquals('HTTP Error 500: a server error', str(err))
      self.assertTrue(isinstance(err.cause, urllib2.HTTPError))
    else:
      self.fail('ServerError expected')

    try:
      trans.send_rpc(self.my_method.remote, request)
    except remote.RequestError, err:
      self.assertEquals('an error', str(err))
      self.assertEquals(None, err.cause)
    else:
      self.fail('RequestError expected')

    try:
      trans.send_rpc(self.my_method.remote, request)
    except remote.ServerError, err:
      self.assertEquals('HTTP Error 500: a text message is here anyway',
                        str(err))
      self.assertTrue(isinstance(err.cause, urllib2.HTTPError))
    else:
      self.fail('ServerError expected')

  def testSendProtobuf(self):
    self.do_test_send_rpc(protobuf)

  def testSendProtojson(self):
    self.do_test_send_rpc(protojson)

  def testURLError(self):
    trans = transport.HttpTransport('http://myserver/myservice',
                                    protocol=protojson)

    urllib2.urlopen(mox.IsA(urllib2.Request)).AndRaise(
      urllib2.URLError('a bad connection'))

    self.mox.ReplayAll()

    request = Message(value=u'The request value')
    try:
      trans.send_rpc(self.my_method.remote, request)
    except remote.NetworkError, err:
      self.assertEquals('a bad connection', str(err))
      self.assertTrue(isinstance(err.cause, urllib2.URLError))
    else:
      self.fail('Network error expected')


def main():
  unittest.main()


if __name__ == '__main__':
  main()
