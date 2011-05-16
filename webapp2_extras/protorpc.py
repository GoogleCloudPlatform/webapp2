# -*- coding: utf-8 -*-
"""
    webapp2_extras.protorpc
    =======================

    Support for Google ProtoRPC library in webapp2.

    Ported from protorpc.service_handlers.

    See: http://code.google.com/p/google-protorpc/

    :copyright: 2010 Google Inc.
    :copyright: 2011 tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
from __future__ import absolute_import

import logging

from protorpc import forms
from protorpc import registry
from protorpc import remote
from protorpc import service_handlers

import webapp2

# The whole method pattern is an optional regex.  It contains a single
# group used for mapping to the query parameter.  This is passed to the
# parameters of 'get' and 'post' on the ServiceHandler.
_METHOD_PATTERN = r'(?:\.([^?]*))?'


class ServiceHandler(webapp2.RequestHandler):
    def __init__(self, request, response):
        self.initialize(request, response)

    def dispatch_service(self, factory, service):
        self.factory = factory
        self.service = service
        # TODO: support mapping with named args?
        # self.request.route_kwargs['service_path']
        # self.request.route_kwargs['remote_method']
        self.handle(self.request.method,
                    self.request.route_args[0],
                    self.request.route_args[1])

    def handle(self, http_method, service_path, remote_method):
        factory = self.factory
        service = self.service
        # Provide server state to the service, uf the service object has an
        # "initialize_request_state" method.
        state_initializer = getattr(service, 'initialize_request_state', None)
        if state_initializer:
            request = self.request
            environ = request.environ
            request_state = remote.HttpRequestState(
                remote_host=environ.get('REMOTE_HOST', None),
                remote_address=environ.get('REMOTE_ADDR', None),
                server_host=environ.get('SERVER_HOST', None),
                server_port=int(environ.get('SERVER_PORT', None)),
                http_method=http_method,
                service_path=service_path,
                headers=[(k, request.headers[k]) for k in request.headers]
            )
            state_initializer(request_state)

        # Search for mapper to mediate request.
        for mapper in factory.all_request_mappers():
            if self.match_request(mapper, http_method, remote_method):
                break
        else:
            message = 'Unrecognized RPC format.'
            logging.error(message)
            self.abort(400, detail=message)

        method = getattr(service, remote_method, None)
        if not method:
            message = 'Unrecognized RPC method: %s' % remote_method
            logging.error(message)
            self.abort(400, detail=message)

        method_info = method.remote
        try:
            request = mapper.build_request(self, method_info.request_type)
        except Exception, e:
            # We catch everything here (e.g., JSON decode errors),
            # differently from protorpc.service_handlers
            logging.error('Error building request: %s', e)
            self.abort(400, detail='Invalid RPC request.')

        try:
            response = method(request)
            mapper.build_response(self, response)
        except Exception, e:
            # We catch everything here (e.g., errors in the service method),
            # differently from protorpc.service_handlers
            logging.error('Error building response: %s', e)
            self.abort(500, detail='Invalid RPC response.')

    def match_request(self, mapper, http_method, remote_method):
        content_type = self.request.content_type
        if not content_type:
            return False

        return bool(
            # Must have remote method name.
            remote_method and
            # Must have allowed HTTP method.
            http_method in mapper.http_methods and
            # Must have correct content type.
            content_type.lower() in mapper.content_types)


class ServiceHandlerFactory(object):
    def __init__(self, service_factory):
        self.service_factory = service_factory
        self.request_mappers = []

    def all_request_mappers(self):
        return iter(self.request_mappers)

    def add_request_mapper(self, mapper):
        self.request_mappers.append(mapper)

    def __call__(self, request, response):
        handler = ServiceHandler(request, response)
        handler.dispatch_service(self, self.service_factory())

    def mapping(self, path):
        if not path.startswith('/') or path.endswith('/'):
            raise ValueError('Path must start with a slash and must not end '
                             'with a slash, got %r.' % path)

        service_url_pattern = r'(%s)%s' % (path, _METHOD_PATTERN)
        return service_url_pattern, self

    @classmethod
    def default(cls, service_factory, parameter_prefix=''):
        factory = cls(service_factory)
        factory.add_request_mapper(
            service_handlers.URLEncodedRPCMapper(parameter_prefix))
        factory.add_request_mapper(service_handlers.ProtobufRPCMapper())
        factory.add_request_mapper(service_handlers.JSONRPCMapper())
        return factory


def service_mapping(services, registry_path=forms.DEFAULT_REGISTRY_PATH):
    if isinstance(services, dict):
        services = services.iteritems()

    mapping = []
    registry_map = {}

    if registry_path is not None:
        registry_service = registry.RegistryService.new_factory(registry_map)
        services = list(services) + [(registry_path, registry_service)]
        mapping.append((registry_path + r'/form(?:/)?',
                        forms.FormsHandler.new_factory(registry_path)))
        mapping.append((registry_path + r'/form/(.+)', forms.ResourceHandler))

    paths = set()
    for service_item in services:
        if isinstance(service_item, (list, tuple)):
            path, service = service_item
            service_class = getattr(service, 'service_class', service)
        else:
            service = service_item
            service_class = getattr(service, 'service_class', service)
            path = '/' + service_class.definition_name().replace('.', '/')

        if path in paths:
            raise service_handlers.ServiceConfigurationError(
                'Path %r is already defined in service mapping'
                % path.encode('utf-8'))
        else:
            paths.add(path)

        # Create service mapping for webapp.
        new_mapping = ServiceHandlerFactory.default(service).mapping(path)
        mapping.append(new_mapping)

        # Update registry with service class.
        registry_map[path] = service_class

    return mapping


def run_services(services, registry_path=forms.DEFAULT_REGISTRY_PATH,
                 debug=False):
    mappings = service_mapping(services, registry_path=registry_path)
    app = webapp2.WSGIApplication(routes=mappings, debug=debug)
    app.run()
