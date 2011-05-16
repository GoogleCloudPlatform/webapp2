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

"""Tests for protorpc.remote."""

__author__ = 'rafek@google.com (Rafe Kaplan)'

import sys
import types
import unittest
from wsgiref import headers

from protorpc import descriptor
from protorpc import message_types
from protorpc import messages
from protorpc import remote
from protorpc import test_util
from protorpc import transport

import mox


class ModuleInterfaceTest(test_util.ModuleInterfaceTest,
                          test_util.TestCase):

  MODULE = remote


class Request(messages.Message):
  """Test request message."""

  value = messages.StringField(1)


class Response(messages.Message):
  """Test response message."""

  value = messages.StringField(1)


class MyService(remote.Service):

  @remote.method(Request, Response)
  def remote_method(self, request):
    response = Response()
    response.value = request.value
    return response


class SimpleRequest(messages.Message):
  """Simple request message type used for tests."""

  param1 = messages.StringField(1)
  param2 = messages.StringField(2)


class SimpleResponse(messages.Message):
  """Simple response message type used for tests."""


class BasicService(remote.Service):
  """A basic service with decorated remote method."""

  def __init__(self):
    self.request_ids = []

  @remote.method(SimpleRequest, SimpleResponse)
  def remote_method(self, request):
    self.request_ids.append(id(request))
    return SimpleResponse()


class RpcErrorTest(test_util.TestCase):

  def testFromStatus(self):
    for state in remote.RpcState:
      exception = remote.RpcError.from_state
    self.assertEquals(remote.ServerError,
                      remote.RpcError.from_state('SERVER_ERROR'))
  

class ApplicationErrorTest(test_util.TestCase):

  def testErrorCode(self):
    self.assertEquals('blam',
                      remote.ApplicationError('an error', 'blam').error_name)

  def testStr(self):
    self.assertEquals('an error', str(remote.ApplicationError('an error', 1)))

  def testRepr(self):
    self.assertEquals("ApplicationError('an error', 1)",
                      repr(remote.ApplicationError('an error', 1)))
      
    self.assertEquals("ApplicationError('an error')",
                      repr(remote.ApplicationError('an error')))
   

class RemoteTest(test_util.TestCase):
  """Test remote method decorator."""

  def testRemote(self):
    """Test use of remote decorator."""
    self.assertEquals(SimpleRequest,
                      BasicService.remote_method.remote.request_type)
    self.assertEquals(SimpleResponse,
                      BasicService.remote_method.remote.response_type)
    self.assertTrue(isinstance(BasicService.remote_method.remote.method,
                               types.FunctionType))

  def testRemoteMessageResolution(self):
    """Test use of remote decorator to resolve message types by name."""
    class OtherService(remote.Service):

      @remote.method('SimpleRequest', 'SimpleResponse')
      def remote_method(self, request):
        pass

    self.assertEquals(SimpleRequest,
                      OtherService.remote_method.remote.request_type)
    self.assertEquals(SimpleResponse,
                      OtherService.remote_method.remote.response_type)

  def testRemoteMessageResolution_NotFound(self):
    """Test failure to find message types."""
    class OtherService(remote.Service):

      @remote.method('NoSuchRequest', 'NoSuchResponse')
      def remote_method(self, request):
        pass

    self.assertRaisesWithRegexpMatch(
      messages.DefinitionNotFoundError,
      'Could not find definition for NoSuchRequest',
      getattr,
      OtherService.remote_method.remote,
      'request_type')

    self.assertRaisesWithRegexpMatch(
      messages.DefinitionNotFoundError,
      'Could not find definition for NoSuchResponse',
      getattr,
      OtherService.remote_method.remote,
      'response_type')

  def testInvocation(self):
    """Test that invocation passes request through properly."""
    service = BasicService()
    request = SimpleRequest()
    self.assertEquals(SimpleResponse(), service.remote_method(request))
    self.assertEquals([id(request)], service.request_ids)

  def testInvocation_WrongRequestType(self):
    """Wrong request type passed to remote method."""
    service = BasicService()

    self.assertRaises(remote.RequestError,
                      service.remote_method,
                      'wrong')

    self.assertRaises(remote.RequestError,
                      service.remote_method,
                      None)

    self.assertRaises(remote.RequestError,
                      service.remote_method,
                      SimpleResponse())

  def testInvocation_WrongResponseType(self):
    """Wrong response type returned from remote method."""

    class AnotherService(object):

      @remote.method(SimpleRequest, SimpleResponse)
      def remote_method(self, unused_request):
        return self.return_this

    service = AnotherService()

    service.return_this = 'wrong'
    self.assertRaises(remote.ServerError,
                      service.remote_method,
                      SimpleRequest())
    service.return_this = None
    self.assertRaises(remote.ServerError,
                      service.remote_method,
                      SimpleRequest())
    service.return_this = SimpleRequest()
    self.assertRaises(remote.ServerError,
                      service.remote_method,
                      SimpleRequest())

  def testBadRequestType(self):
    """Test bad request types used in remote definition."""

    for request_type in (None, 1020, messages.Message, str):

      def declare():
        class BadService(object):

          @remote.method(request_type, SimpleResponse)
          def remote_method(self, request):
            pass

      self.assertRaises(TypeError, declare)

  def testBadResponseType(self):
    """Test bad response types used in remote definition."""

    for response_type in (None, 1020, messages.Message, str):

      def declare():
        class BadService(object):

          @remote.method(SimpleRequest, response_type)
          def remote_method(self, request):
            pass

      self.assertRaises(TypeError, declare)


class GetRemoteMethodTest(test_util.TestCase):
  """Test for is_remote_method."""

  def testGetRemoteMethod(self):
    """Test valid remote method detection."""

    class Service(object):

      @remote.method(Request, Response)
      def remote_method(self, request):
        pass

    self.assertEquals(Service.remote_method.remote,
                      remote.get_remote_method_info(Service.remote_method))
    self.assertTrue(Service.remote_method.remote,
                    remote.get_remote_method_info(Service().remote_method))

  def testGetNotRemoteMethod(self):
    """Test positive result on a remote method."""

    class NotService(object):

      def not_remote_method(self, request):
        pass

    def fn(self):
      pass

    class NotReallyRemote(object):
      """Test negative result on many bad values for remote methods."""

      def not_really(self, request):
        pass

      not_really.remote = 'something else'

    for not_remote in [NotService.not_remote_method,
                       NotService().not_remote_method,
                       NotReallyRemote.not_really,
                       NotReallyRemote().not_really,
                       None,
                       1,
                       'a string',
                       fn]:
      self.assertEquals(None, remote.get_remote_method_info(not_remote))


class RequestStateTest(test_util.TestCase):
  """Test request state."""

  STATE_CLASS = remote.RequestState

  def testConstructor(self):
    """Test constructor."""
    state = self.STATE_CLASS(remote_host='remote-host',
                             remote_address='remote-address',
                             server_host='server-host',
                             server_port=10)
    self.assertEquals('remote-host', state.remote_host)
    self.assertEquals('remote-address', state.remote_address)
    self.assertEquals('server-host', state.server_host)
    self.assertEquals(10, state.server_port)

    state = self.STATE_CLASS()
    self.assertEquals(None, state.remote_host)
    self.assertEquals(None, state.remote_address)
    self.assertEquals(None, state.server_host)
    self.assertEquals(None, state.server_port)

  def testConstructorError(self):
    """Test unexpected keyword argument."""
    self.assertRaises(TypeError,
                      self.STATE_CLASS,
                      x=10)

  def testRepr(self):
    """Test string representation."""
    self.assertEquals('<%s>' % self.STATE_CLASS.__name__,
                      repr(self.STATE_CLASS()))
    self.assertEquals("<%s remote_host='abc'>" % self.STATE_CLASS.__name__,
                      repr(self.STATE_CLASS(remote_host='abc')))
    self.assertEquals("<%s remote_host='abc' "
                      "remote_address='def'>" % self.STATE_CLASS.__name__,
                      repr(self.STATE_CLASS(remote_host='abc',
                                               remote_address='def')))
    self.assertEquals("<%s remote_host='abc' "
                      "remote_address='def' "
                      "server_host='ghi'>" % self.STATE_CLASS.__name__,
                      repr(self.STATE_CLASS(remote_host='abc',
                                            remote_address='def',
                                            server_host='ghi')))
    self.assertEquals("<%s remote_host='abc' "
                      "remote_address='def' "
                      "server_host='ghi' "
                      'server_port=102>' % self.STATE_CLASS.__name__,
                      repr(self.STATE_CLASS(remote_host='abc',
                                            remote_address='def',
                                            server_host='ghi',
                                            server_port=102)))


class HttpRequestStateTest(RequestStateTest):

  STATE_CLASS = remote.HttpRequestState

  def testHttpMethod(self):
    state = remote.HttpRequestState(http_method='GET')
    self.assertEquals('GET', state.http_method)

  def testHttpMethod(self):
    state = remote.HttpRequestState(service_path='/bar')
    self.assertEquals('/bar', state.service_path)

  def testHeadersList(self):
    state = remote.HttpRequestState(
      headers=[('a', 'b'), ('c', 'd'), ('c', 'e')])

    self.assertEquals(['a', 'c', 'c'], state.headers.keys())
    self.assertEquals(['b'], state.headers.get_all('a'))
    self.assertEquals(['d', 'e'], state.headers.get_all('c'))

  def testHeadersDict(self):
    state = remote.HttpRequestState(headers={'a': 'b', 'c': ['d', 'e']})

    self.assertEquals(['a', 'c', 'c'], sorted(state.headers.keys()))
    self.assertEquals(['b'], state.headers.get_all('a'))
    self.assertEquals(['d', 'e'], state.headers.get_all('c'))

  def testRepr(self):
    super(HttpRequestStateTest, self).testRepr()

    self.assertEquals("<%s remote_host='abc' "
                      "remote_address='def' "
                      "server_host='ghi' "
                      'server_port=102 '
                      "http_method='POST' "
                      "service_path='/bar' "
                      "headers=[('a', 'b'), ('c', 'd')]>" %
                      self.STATE_CLASS.__name__,
                      repr(self.STATE_CLASS(remote_host='abc',
                                            remote_address='def',
                                            server_host='ghi',
                                            server_port=102,
                                            http_method='POST',
                                            service_path='/bar',
                                            headers={'a': 'b', 'c': 'd'},
                                            )))


class ServiceTest(test_util.TestCase):
  """Test Service class."""

  def testServiceBase_AllRemoteMethods(self):
    """Test that service base class has no remote methods."""
    self.assertEquals({}, remote.Service.all_remote_methods())

  def testAllRemoteMethods(self):
    """Test all_remote_methods with properly Service subclass."""
    self.assertEquals({'remote_method': MyService.remote_method},
                      MyService.all_remote_methods())

  def testAllRemoteMethods_SubClass(self):
    """Test all_remote_methods on a sub-class of a service."""
    class SubClass(MyService):

      @remote.method(Request, Response)
      def sub_class_method(self, request):
        pass

    self.assertEquals({'remote_method': SubClass.remote_method,
                       'sub_class_method': SubClass.sub_class_method,
                      },
                      SubClass.all_remote_methods())

  def testOverrideMethod(self):
    """Test that trying to override a remote method with remote decorator."""
    class SubClass(MyService):

      def remote_method(self, request):
        pass

    self.assertEquals({'remote_method': SubClass.remote_method,
                      },
                      SubClass.all_remote_methods())

  def testOverrideMethodWithRemote(self):
    """Test trying to override a remote method with remote decorator."""
    def do_override():
      class SubClass(MyService):

        @remote.method(Request, Response)
        def remote_method(self, request):
          pass

    self.assertRaisesWithRegexpMatch(remote.ServiceDefinitionError,
                                     'Do not use remote decorator when '
                                     'overloading remote method remote_method '
                                     'on service SubClass',
                                     do_override)

  def testOverrideMethodWithInvalidValue(self):
    """Test trying to override a remote method with remote decorator."""
    def do_override(bad_value):
      class SubClass(MyService):

        remote_method = bad_value

    for bad_value in [None, 1, 'string', {}]:
      self.assertRaisesWithRegexpMatch(remote.ServiceDefinitionError,
                                       'Must override remote_method in '
                                       'SubClass with a method',
                                       do_override, bad_value)

  def testCallingRemoteMethod(self):
    """Test invoking a remote method."""
    expected = Response()
    expected.value = 'what was passed in'

    request = Request()
    request.value = 'what was passed in'

    service = MyService()
    self.assertEquals(expected, service.remote_method(request))

  def testFactory(self):
    """Test using factory to pass in state."""
    class StatefulService(remote.Service):

      def __init__(self, a, b, c=None):
        self.a = a
        self.b = b
        self.c = c

    state = [1, 2, 3]

    factory = StatefulService.new_factory(1, state)

    self.assertEquals('Creates new instances of service StatefulService.\n\n'
                      'Returns:\n'
                      '  New instance of __main__.StatefulService.',
                      factory.func_doc)
    self.assertEquals('StatefulService_service_factory', factory.func_name)
    self.assertEquals(StatefulService, factory.service_class)

    service = factory()
    self.assertEquals(1, service.a)
    self.assertEquals(id(state), id(service.b))
    self.assertEquals(None, service.c)

    factory = StatefulService.new_factory(2, b=3, c=4)
    service = factory()
    self.assertEquals(2, service.a)
    self.assertEquals(3, service.b)
    self.assertEquals(4, service.c)

  def testFactoryError(self):
    """Test misusing a factory."""
    # Passing positional argument that is not accepted by class.
    self.assertRaises(TypeError, remote.Service.new_factory(1))

    # Passing keyword argument that is not accepted by class.
    self.assertRaises(TypeError, remote.Service.new_factory(x=1))

    class StatefulService(remote.Service):

      def __init__(self, a):
        pass

    # Missing required parameter.
    self.assertRaises(TypeError, StatefulService.new_factory())

  def testDefinitionName(self):
    """Test getting service definition name."""
    class TheService(remote.Service):
      pass

    self.assertEquals('remote_test.TheService', TheService.definition_name())
    self.assertEquals('remote_test', TheService.outer_definition_name())
    self.assertEquals('remote_test', TheService.definition_package())

  def testDefinitionNameWithPackage(self):
    """Test getting service definition name when package defined."""
    global package
    package = 'my.package'
    try:
      class TheService(remote.Service):
        pass

      self.assertEquals('my.package.TheService', TheService.definition_name())
      self.assertEquals('my.package', TheService.outer_definition_name())
      self.assertEquals('my.package', TheService.definition_package())
    finally:
      del package

  def testDefinitionNameWithNoModule(self):
    """Test getting service definition name when package defined."""
    module = sys.modules[__name__]
    try:
      del sys.modules[__name__]
      class TheService(remote.Service):
        pass

      self.assertEquals('TheService', TheService.definition_name())
      self.assertEquals(None, TheService.outer_definition_name())
      self.assertEquals(None, TheService.definition_package())
    finally:
      sys.modules[__name__] = module


class StubTest(test_util.TestCase):

  def setUp(self):
    self.mox = mox.Mox()
    self.transport = self.mox.CreateMockAnything()

  def testDefinitionName(self):
    self.assertEquals(BasicService.definition_name(),
                      BasicService.Stub.definition_name())
    self.assertEquals(BasicService.outer_definition_name(),
                      BasicService.Stub.outer_definition_name())
    self.assertEquals(BasicService.definition_package(),
                      BasicService.Stub.definition_package())

  def testRemoteMethods(self):
    self.assertEquals(BasicService.all_remote_methods(),
                      BasicService.Stub.all_remote_methods())

  def testSync_WithRequest(self):
    stub = BasicService.Stub(self.transport)

    request = SimpleRequest()
    request.param1 = 'val1'
    request.param2 = 'val2'
    response = SimpleResponse()

    rpc = transport.Rpc(request)
    rpc.set_response(response)
    self.transport.send_rpc(BasicService.remote_method.remote,
                            request).AndReturn(rpc)

    self.mox.ReplayAll()

    self.assertEquals(SimpleResponse(), stub.remote_method(request))

    self.mox.VerifyAll()

  def testSync_WithKwargs(self):
    stub = BasicService.Stub(self.transport)


    request = SimpleRequest()
    request.param1 = 'val1'
    request.param2 = 'val2'
    response = SimpleResponse()

    rpc = transport.Rpc(request)
    rpc.set_response(response)
    self.transport.send_rpc(BasicService.remote_method.remote,
                            request).AndReturn(rpc)

    self.mox.ReplayAll()

    self.assertEquals(SimpleResponse(), stub.remote_method(param1='val1',
                                                           param2='val2'))

    self.mox.VerifyAll()

  def testAsync_WithRequest(self):
    stub = BasicService.Stub(self.transport)

    request = SimpleRequest()
    request.param1 = 'val1'
    request.param2 = 'val2'
    response = SimpleResponse()

    rpc = transport.Rpc(request)

    self.transport.send_rpc(BasicService.remote_method.remote,
                            request).AndReturn(rpc)

    self.mox.ReplayAll()

    self.assertEquals(rpc, stub.async.remote_method(request))

    self.mox.VerifyAll()

  def testAsync_WithKwargs(self):
    stub = BasicService.Stub(self.transport)

    request = SimpleRequest()
    request.param1 = 'val1'
    request.param2 = 'val2'
    response = SimpleResponse()

    rpc = transport.Rpc(request)

    self.transport.send_rpc(BasicService.remote_method.remote,
                            request).AndReturn(rpc)

    self.mox.ReplayAll()

    self.assertEquals(rpc, stub.async.remote_method(param1='val1',
                                                    param2='val2'))

    self.mox.VerifyAll()

  def testAsync_WithRequestAndKwargs(self):
    stub = BasicService.Stub(self.transport)

    request = SimpleRequest()
    request.param1 = 'val1'
    request.param2 = 'val2'
    response = SimpleResponse()

    self.mox.ReplayAll()

    self.assertRaisesWithRegexpMatch(
      TypeError,
      r'May not provide both args and kwargs',
      stub.async.remote_method,
      request,
      param1='val1',
      param2='val2')

    self.mox.VerifyAll()

  def testAsync_WithTooManyPositionals(self):
    stub = BasicService.Stub(self.transport)

    request = SimpleRequest()
    request.param1 = 'val1'
    request.param2 = 'val2'
    response = SimpleResponse()

    self.mox.ReplayAll()

    self.assertRaisesWithRegexpMatch(
      TypeError,
      r'remote_method\(\) takes at most 2 positional arguments \(3 given\)',
      stub.async.remote_method,
      request, 'another value')

    self.mox.VerifyAll()


class IsErrorStatusTest(test_util.TestCase):

  def testIsError(self):
    for state in (s for s in remote.RpcState if s > remote.RpcState.RUNNING):
      status = remote.RpcStatus(state=state)
      self.assertTrue(remote.is_error_status(status))

  def testIsNotError(self):
    for state in (s for s in remote.RpcState if s <= remote.RpcState.RUNNING):
      status = remote.RpcStatus(state=state)
      self.assertFalse(remote.is_error_status(status))

  def testStateNone(self):
    self.assertRaises(messages.ValidationError,
                      remote.is_error_status, remote.RpcStatus())


class CheckRpcStatusTest(test_util.TestCase):

  def testStateNone(self):
    self.assertRaises(messages.ValidationError,
                      remote.check_rpc_status, remote.RpcStatus())

  def testNoError(self):
    for state in (remote.RpcState.OK, remote.RpcState.RUNNING):
      remote.check_rpc_status(remote.RpcStatus(state=state))

  def testErrorState(self):
    status = remote.RpcStatus(state=remote.RpcState.REQUEST_ERROR,
                              error_message='a request error')
    self.assertRaisesWithRegexpMatch(remote.RequestError,
                                     'a request error',
                                     remote.check_rpc_status, status)

  def testApplicationErrorState(self):
    status = remote.RpcStatus(state=remote.RpcState.APPLICATION_ERROR,
                              error_message='an application error',
                              error_name='blam')
    try:
      remote.check_rpc_status(status)
      self.fail('Should have raised application error.')
    except remote.ApplicationError, err:
      self.assertEquals('an application error', str(err))
      self.assertEquals('blam', err.error_name)


def main():
  unittest.main()


if __name__ == '__main__':
  main()
