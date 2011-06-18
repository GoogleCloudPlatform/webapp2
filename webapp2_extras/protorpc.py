# -*- coding: utf-8 -*-
"""
    webapp2_extras.protorpc
    =======================

    Support for Google ProtoRPC library in webapp2.

    Ported from protorpc.service_handlers.

    See: http://code.google.com/p/google-protorpc/

    .. warning::
       This is an experimental package, as the ProtoRPC API is not stable yet.

    :copyright: 2010 Google Inc.
    :copyright: 2011 tipfy.org.
    :license: Apache Sotware License, see LICENSE for details.
"""
from __future__ import absolute_import

import logging

from protorpc import registry
from protorpc.webapp import service_handlers
from protorpc.webapp import forms

import webapp2


class ServiceHandler(webapp2.RequestHandler, service_handlers.ServiceHandler):
    def dispatch(self, factory, service):
        # Unfortunately we need to access the protected attributes.
        self._ServiceHandler__factory = factory
        self._ServiceHandler__service = service

        request = self.request
        method = getattr(self, request.method.lower(), None)
        service_path, remote_method = request.route_args
        if method:
            self.handle(request.method, service_path, remote_method)
        else:
            message = 'Unsupported HTTP method: %s' % request.method
            logging.error(message)
            self.response.set_status(405, message)

        if request.method == 'GET':
            status = self.response.status_int
            if status in (405, 415) or not request.content_type:
                self._ServiceHandler__show_info(service_path, remote_method)


class ServiceHandlerFactory(service_handlers.ServiceHandlerFactory):
    def __call__(self, request, response):
        """Construct a new service handler instance."""
        handler = ServiceHandler(request, response)
        handler.dispatch(self, self.service_factory())


def _normalize_services(mixed_services):
    if isinstance(mixed_services, dict):
        mixed_services = mixed_services.iteritems()

    services = []
    for service_item in mixed_services:
        if isinstance(service_item, (list, tuple)):
            path, service = service_item
        else:
            path = None
            service = service_item

        if isinstance(service, basestring):
            # Lazily import the service class.
            service = webapp2.import_string(service)

        services.append((path, service))

    return services


def service_mapping(services, registry_path=forms.DEFAULT_REGISTRY_PATH):
    # TODO: clean the convoluted API? Accept services as tuples only, or
    # make different functions to accept different things.
    # For now we are just following the same API from protorpc.
    services = _normalize_services(services)

    mapping = []
    registry_map = {}

    if registry_path is not None:
        registry_service = registry.RegistryService.new_factory(registry_map)
        services = list(services) + [(registry_path, registry_service)]
        forms_handler = forms.FormsHandler(registry_path=registry_path)
        mapping.append((registry_path + r'/form(?:/)?', forms_handler))
        mapping.append((registry_path + r'/form/(.+)', forms.ResourceHandler))

    paths = set()
    for path, service in services:
        service_class = getattr(service, 'service_class', service)
        if not path:
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
    """Handle CGI request using service mapping.

    Parameters are the same as :func:`service_mapping`.
    """
    mappings = service_mapping(services, registry_path=registry_path)
    app = webapp2.WSGIApplication(routes=mappings, debug=debug)
    app.run()
