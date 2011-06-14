import cgi
import unittest
import urllib2
from wsgiref import simple_server
from wsgiref import validate

from protorpc import end2end_test
from protorpc.experimental import filters
from protorpc.experimental import util as wsgi_util
from protorpc.experimental import wsgi_service
from protorpc import protojson
from protorpc import test_util
from protorpc import transport
from protorpc import webapp_test_util


def app_mapping(mapping, on_error=filters.HTTP_NOT_FOUND):
  application = on_error
  for path, app in reversed(mapping):
    application = wsgi_service.match_method(path,
                                            app=app,
                                            on_error=application)
  return application


class ServiceAppTest(end2end_test.EndToEndTest):

  def tearDown(self):
    self.server.shutdown()

  def StartWebServer(self, port):
    """Start web server."""
    protocols = wsgi_util.Protocols()
    protocols.add_protocol(protojson, 'json', 'application/json')

    application = wsgi_service.service_app(webapp_test_util.TestService,
                                           protocols=protocols)
    validated_application = validate.validator(application)

    other_application = wsgi_service.service_app(
      webapp_test_util.TestService.new_factory('initialized'),
      protocols=protocols)
    other_validated_application = validate.validator(other_application)

    applications = app_mapping([
      ('/my/service', validated_application),
      ('/my/other_service', other_validated_application),
    ])
    
    server = simple_server.make_server('localhost', port, applications)
    server = webapp_test_util.ServerThread(server)
    server.start()
    server.wait_until_running()
    return server, application



if __name__ == '__main__':
  unittest.main()
