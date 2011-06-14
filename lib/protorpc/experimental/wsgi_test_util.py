import urllib2
from wsgiref import simple_server
from wsgiref import validate

from protorpc import test_util
from protorpc import webapp_test_util


class FiltersTestBase(test_util.TestCase):

  def setUp(self):
    self.server = None

  def tearDown(self):
    if self.server:
      self.server.shutdown()
  
  def StartWebServer(self, application):
    """Start web server."""
    self.port = test_util.pick_unused_port()
    self.server_url = 'http://localhost:%d' % self.port
    validated_application = validate.validator(application)
    server = simple_server.make_server('localhost',
                                       self.port,
                                       validated_application)
    server = webapp_test_util.ServerThread(server)
    server.start()
    server.wait_until_running()
    self.server = server
    self.application = application

  def SendRequest(self, path, content='', headers=None):
    headers_dict = {
      'content-type': 'application/json',
    }
    headers_dict.update(headers or {})
    self.server.handle_request()
    return urllib2.urlopen(
      urllib2.Request(self.server_url + path, content, headers_dict))

  def CheckHeaders(self, expected_headers, headers):
    expected_headers = expected_headers or {}

    # Check expected headers.
    checked_headers = set()
    for name, expected_value in expected_headers.iteritems():
      checked_headers.add(name)
      self.assertEquals(expected_value, headers.get(name))
    missing_headers = set(expected_headers) - checked_headers

    if missing_headers:
      self.fail('Response did not contain headers %r' % missing_headers)

  def CheckResponse(self, response, code=200, expected_content='',
                    content_type=None,
                    expected_headers=None,
                    expected_content_type=None):
    expected_headers = expected_headers or {}
    expected_headers['content-length'] = str(len(expected_content))
    expected_headers['content-type'] = expected_content_type or 'text/html'
    self.assertEquals(code, response.code)
    self.assertEquals(expected_content, response.read())
    response_headers = dict(response.info().items())
    self.CheckHeaders(expected_headers, response_headers)

  def CheckError(self, path, content='', headers=None,
                 expected_code=400, expected_content='',
                 expected_headers=None, expected_content_type=None):
    try:
      self.SendRequest(path, content, headers)
      self.fail('Expected request to fail')
    except urllib2.HTTPError, err:
      self.assertEquals(expected_code, err.code)
      expected_headers = expected_headers or {}
      expected_headers['content-type'] = expected_content_type or 'text/html'
      expected_headers['content-length'] = str(len(expected_content))
      self.CheckHeaders(expected_headers,
                        dict(err.hdrs.items()))
