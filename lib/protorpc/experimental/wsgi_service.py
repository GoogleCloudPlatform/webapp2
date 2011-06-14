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

import cgi
import logging
import re

from wsgiref import headers as wsgi_headers

from protorpc.experimental import util as exp_util
from protorpc.experimental import filters
from protorpc import messages
from protorpc import remote
from protorpc import util

__all__ = [
  'service_app',
]

_METHOD_PATTERN = r'(?:\.([^?]*))?'

PROTOCOLS_ENVIRON = 'protorpc.protocols'
REQUEST_PROTOCOL_ENVIRON = 'protorpc.request.protocol'
RESPONSE_PROTOCOL_ENVIRON = 'protorpc.response.protocol'
SERVICE_PATH_ENVIRON = 'protorpc.service.path'
METHOD_NAME_ENVIRON = 'protorpc.method.name'

WSGI_TRACE_ENVIRON = 'protorpc.wsgi.trace'

def wsgi_trace(description):
  def wsgi_trace_decorator(app):
    def wsgi_trace_wrapper(environ, start_response):
      outer_trace = False
      tracer = environ.get(WSGI_TRACE_ENVIRON)
      if tracer is None:
        tracer = []
        environ[WSGI_TRACE_ENVIRON] = tracer
        outer_trace = True
      try:
        return app(environ, start_response)
      finally:
        tracer.append(description)
        if outer_trace:
          del environ[WSGI_TRACE_ENVIRON]
          trace_string = '\n'.join('  %s' % trace for trace in tracer)
          logging.debug('WSGI Trace:\n%s', trace_string)
    return wsgi_trace_wrapper
  return wsgi_trace_decorator


def use_protocols(protocols, app=filters.HTTP_OK):
  @wsgi_trace('Use protocols %r' % (protocols.names,))
  def use_protocols_middleware(environ, start_request):
    environ[PROTOCOLS_ENVIRON] = protocols
    return app(environ, start_request)
  return use_protocols_middleware


def match_protocol(app=filters.HTTP_OK, protocols=None):
  @wsgi_trace('Matching protocols')
  def match_protocol_middleware(environ, start_response):
    # Make sure there is a content-type.
    content_type = environ.get('CONTENT_TYPE')
    if not content_type:
      #content_type = environ.get('HTTP_CONTENT_TYPE')
      if not content_type:
        return filters.HTTP_BAD_REQUEST(environ, start_response)

    content_type, _ = cgi.parse_header(content_type)
    protocols = environ.get(PROTOCOLS_ENVIRON)
    if not protocols:
      raise Exception('Protocols are not configured in WSGI chain')

    try:
      config = protocols.lookup_by_content_type(content_type)
    except KeyError:
      return filters.HTTP_UNSUPPORTED_MEDIA_TYPE(environ, start_response)

    environ[REQUEST_PROTOCOL_ENVIRON] = config
    environ[RESPONSE_PROTOCOL_ENVIRON] = config

    return app(environ, start_response)

  if protocols:
    return use_protocols(protocols, match_protocol_middleware)
  else:
    return match_protocol_middleware


@util.positional(1)
def match_method(service_path=None,
                 app=filters.HTTP_OK,
                 on_error=filters.HTTP_NOT_FOUND):
  if service_path is None:
    service_path = r'[^.]*'
  match_regex = re.compile(r'^(%s)%s$' % (service_path, _METHOD_PATTERN))
  @wsgi_trace('Match method on service-path %s' % service_path)
  def match_method_middleware(environ, start_response):
    path_info = environ['PATH_INFO']
    match = match_regex.match(path_info)
    if not match:
      return on_error(environ, start_response)
    else:
      environ[SERVICE_PATH_ENVIRON] = match.group(1)
      environ[METHOD_NAME_ENVIRON] = match.group(2)
    return app(environ, start_response)
  return match_method_middleware
      

def protorpc_response(message, protocol, *args, **kwargs):
  encoded_message = protocol.encode_message(message)
  return filters.static_page(encoded_message,
                             content_type=protocol.CONTENT_TYPE,
                             *args,
                             **kwargs)


@util.positional(2)
def service_app(service_factory,
                service_path=None,
                app=None,
                protocols=None):
  if isinstance(service_factory, type):
    service_class = service_factory
  else:
    service_class = service_factory.service_class

  if service_path is None:
    if app is not None:
      raise filters.ServiceConfigurationError(
        'Do not provide default application for service with no '
        'explicit service path')

  app = app or filters.HTTP_NOT_FOUND

  @wsgi_trace('Service application %s' % (service_class.__name__))
  def service_app_application(environ, start_response):
    def get_environ(name):
      value = environ.get(name)
      if not value:
        raise Exception('Value for %s missing from quest environment' % name)
      return value

    # Get necessary pieces from the environment.
    method_name = get_environ(METHOD_NAME_ENVIRON)
    service_path = get_environ(SERVICE_PATH_ENVIRON)
    request_protocol = get_environ(REQUEST_PROTOCOL_ENVIRON)

    # New service instance.
    service_instance = service_factory()
    try:
      initialize_request_state = service_instance.initialize_request_state
    except AttributeError:
      pass
    else:
      header_list = []
      for name, value in environ.iteritems():
        if name.startswith('HTTP_'):
          header_list.append((
            name[len('HTTP_'):].lower().replace('_', '-'), value))
      initialize_request_state(remote.HttpRequestState(
        http_method='POST',
        service_path=service_path,
        headers=header_list,
        remote_host=environ.get('REMOTE_HOST', None),
        remote_address=environ.get('REMOTE_ADDR', None),
        server_host=environ.get('SERVER_HOST', None)))

    # Resolve method.
    try:
      method = getattr(service_instance, method_name)
    except AttributeError:
      response_app = protorpc_response(
        remote.RpcStatus(
          state=remote.RpcState.METHOD_NOT_FOUND_ERROR,
          error_message='Unrecognized RPC method: %s' % method_name),
          protocol=request_protocol.protocol,
        status=(400, 'Bad Request'))
      return response_app(environ, start_response)

    try:
      remote_info = getattr(method, 'remote')
    except AttributeError:
      return filters.HTTP_BAD_REQUEST(environ, start_response)

    request_type = remote_info.request_type

    # Parse request.
    body = environ['wsgi.input']
    content = body.read(int(environ['CONTENT_LENGTH']))
    try:
      request = request_protocol.protocol.decode_message(request_type, content)
    except (messages.DecodeError, messages.ValidationError), err:
      response_app = protorpc_response(
        remote.RpcStatus(
          state=remote.RpcState.REQUEST_ERROR,
          error_message=('Error parsing ProtoRPC request '
                         '(Unable to parse request content: %s)' % err)),
        protocol=request_protocol.protocol,
        status=(400, 'Bad Request'))
      return response_app(environ, start_response)

    # Execute method.
    try:
      try:
        response = method(request)
      except remote.ApplicationError, err:
        response_app = protorpc_response(
          remote.RpcStatus(
            state=remote.RpcState.APPLICATION_ERROR,
            error_message=err.message,
            error_name=err.error_name),
          protocol=request_protocol.protocol,
          status=(400, 'Bad Request'))
        return response_app(environ, start_response)

      # Build and send response.

      encoded_response = request_protocol.protocol.encode_message(response)
    except Exception, err:
      response_app = protorpc_response(
        remote.RpcStatus(
          state=remote.RpcState.SERVER_ERROR,
          error_message='Internal Server Error'),
        protocol=request_protocol.protocol,
        status=(500, 'Internal Server Error'))
      return response_app(environ, start_response)

    start_response('200 OK',
                   [('content-type', request_protocol.default_content_type),
                    ('content-length', str(len(encoded_response)))])
    return [encoded_response]

  application = service_app_application

  # Must be POST.
  application = filters.environ_equals('REQUEST_METHOD', 'POST',
                                       app=application,
                                       on_error=filters.HTTP_METHOD_NOT_ALLOWED)

  # Match protocol based on content-type.
  application = match_protocol(application, protocols)

  # Must match request path.  Parses out actual service-path.  A non-match is
  # akin to a 404 by default.  Will pass through to next application on miss.
  application = match_method(service_path, app=application, on_error=app)

  return application
