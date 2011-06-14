import cgi
import unittest
import urllib2
from wsgiref import simple_server
from wsgiref import validate

from protorpc.experimental import filters
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
    expected_headers['content-type'] = (
      expected_content_type or 'text/html; charset=utf-8')
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
      expected_headers['content-type'] = (
        expected_content_type or 'text/html; charset=utf-8')
      expected_headers['content-length'] = str(len(expected_content))
      self.CheckHeaders(expected_headers,
                        dict(err.hdrs.items()))


class StaticPageTest(FiltersTestBase):

  def testDefault(self):
    self.StartWebServer(filters.HTTP_OK)
    self.CheckResponse(self.SendRequest('/'))

  def testStatusPair(self):
    self.StartWebServer(filters.static_page(status=(200, 'Okeedokee')))
    self.CheckResponse(self.SendRequest('/'))
      
  def testContent(self):
    self.StartWebServer(filters.static_page('hello world'))
    self.CheckResponse(self.SendRequest('/'), expected_content='hello world')

  def testContentType(self):
    self.StartWebServer(filters.static_page('hello world',
                                            content_type='application/json'))
    self.CheckResponse(self.SendRequest('/'),
                       expected_content='hello world',
                       expected_content_type='application/json')

  def testHeaders(self):
    self.StartWebServer(filters.static_page('hello world',
                                            headers={'a': 'b', 'c': 'd'}))
    self.CheckResponse(self.SendRequest('/'),
                       expected_content='hello world',
                       expected_headers={'a': 'b', 'c': 'd'})

  def testHeadersList(self):
    self.StartWebServer(filters.static_page('hello world',
                                            headers=[('a', 'b'), ('c', 'd')]))
    self.CheckResponse(self.SendRequest('/'),
                       expected_content='hello world',
                       expected_headers={'a': 'b', 'c': 'd'})

  def testErrorContent(self):
    self.StartWebServer(filters.static_page(status='400 Badness',
                                            content='kaboom'))
    self.CheckError('/', expected_content='kaboom')

  def testErrorStatusString(self):
    self.StartWebServer(filters.static_page(status='400 Badness'))
    self.CheckError('/')

  def testErrorStatusTuple(self):
    self.StartWebServer(filters.static_page(status=(402, 'Badness')))
    self.CheckError('/', expected_code=402)

  def testErrorStatusStringAlternateCode(self):
    self.StartWebServer(filters.static_page(status='500 Badness'))
    self.CheckError('/', expected_code=500)

  def testErrorContentType(self):
    self.StartWebServer(filters.static_page(status='400 Badness',
                                            content_type='text/plain'))
    self.CheckError('/', expected_content_type='text/plain')


class FilterRequestTest(FiltersTestBase):

  def testDefaultFilterTrue(self):
    self.StartWebServer(filters.filter_request(lambda environ: True))
    self.CheckResponse(self.SendRequest('/'))

  def testDefaultFilterFalse(self):
    self.StartWebServer(filters.filter_request(lambda environ: False))
    self.CheckError('/')
 
  def testDefaultFilterAlternateApplication(self):
    application = filters.static_page(content='it was ok')
    self.StartWebServer(filters.filter_request(lambda environ: True,
                                               app=application))
    response = self.SendRequest('/')
    self.CheckResponse(response, expected_content='it was ok')
 
  def testDefaultFilterAlternateError(self):
    application = filters.static_page(content='it went awry',
                                      status=(500, 'oh no!'))
    self.StartWebServer(filters.filter_request(lambda environ: True,
                                               app=application))
    self.CheckError('/', content='it went arwy', expected_code=500,
                    expected_content='it went arwy')


class FilterEnvironTest(FiltersTestBase):

  def testFilterEnviron(self):
    ok = filters.static_page('it was ok')
    self.was_run = False
    def filter(value):
      self.was_run = True
      self.assertEquals('POST', value)
      return True

    self.StartWebServer(filters.filter_environ('REQUEST_METHOD',
                                               filter, app=ok))
    response = self.SendRequest('/')
    self.CheckResponse(response, expected_content='it was ok')
    self.assertTrue(self.was_run)

  def testFilterEnvironError(self):
    bad = filters.static_page('it was bad', status=(402, 'Bad'))
    self.was_run = False
    def filter(value):
      self.was_run = True
      self.assertEquals('POST', value)
      return False

    self.StartWebServer(filters.filter_environ('REQUEST_METHOD',
                                               filter, on_error=bad))
    self.CheckError('/', expected_content='it was bad', expected_code=402)
    self.assertTrue(self.was_run)


class FilterHeaderTest(FiltersTestBase):

  def testFilterEnviron(self):
    ok = filters.static_page('it was ok')
    self.was_run = False
    def filter(value):
      self.was_run = True
      self.assertEquals('set', value)
      return True

    self.StartWebServer(filters.filter_header('x',
                                               filter, app=ok))
    response = self.SendRequest('/', headers={'x': 'set'})
    self.CheckResponse(response, expected_content='it was ok')
    self.assertTrue(self.was_run)

  def testFilterEnvironError(self):
    bad = filters.static_page('it was bad', status=(402, 'Bad'))
    self.was_run = False
    def filter(value):
      self.was_run = True
      self.assertEquals(None, value)
      return False

    self.StartWebServer(filters.filter_environ('x',
                                               filter, on_error=bad))
    self.CheckError('/', expected_content='it was bad', expected_code=402)
    self.assertTrue(self.was_run)


class ExpectHeaderTest(FiltersTestBase):

  def testHasHeader(self):
    ok = filters.static_page('it was ok')
    self.StartWebServer(filters.expect_header('x-whatever', app=ok))
    response = self.SendRequest('/', headers={'x-whatever': 'does not matter'})
    self.CheckResponse(response, expected_content='it was ok')

  def testDoesNotHaveError(self):
    not_ok = filters.static_page(status=(401, 'it was bad'))
    self.StartWebServer(filters.expect_header('x-whatever', on_error=not_ok))
    self.CheckError('/', expected_code=401)


class SetEnvironTest(FiltersTestBase):

  def testSetEnviron(self):
    def echo_environ(environ, start_response):
      return filters.static_page(environ['x'])(environ, start_response)
    self.StartWebServer(filters.set_environ('x', 'blar', app=echo_environ))
    response = self.SendRequest('/')
    self.CheckResponse(response, expected_content='blar')


class SetHeaderTest(FiltersTestBase):

  def testSetHeader(self):
    def echo_header(environ, start_response):
      return filters.static_page(environ['HTTP_X'])(environ, start_response)
    self.StartWebServer(filters.set_header('x', 'blar', app=echo_header))
    response = self.SendRequest('/')
    self.CheckResponse(response, expected_content='blar')


class EnvironEqualsTest(FiltersTestBase):

  def testEnvironEquals(self):
    self.StartWebServer(filters.environ_equals('HTTP_X', 'a thing'))
    response = self.SendRequest('/', headers={'x': 'a thing'})
    self.CheckResponse(response, expected_content='')

  def testEnvironEqualsError(self):
    self.StartWebServer(filters.environ_equals('HTTP_X', 'blar'))
    self.CheckError('/', headers={'x': 'a thing'})


class ExpectEnvironTest(FiltersTestBase):

  def testExpectEnviron(self):
    self.StartWebServer(filters.expect_environ('HTTP_X'))
    response = self.SendRequest('/', headers={'x': 'a thing'})
    self.CheckResponse(response, expected_content='')

  def testExpectEnvironError(self):
    self.StartWebServer(filters.expect_environ('HTTP_X'))
    self.CheckError('/')


class MatchEnvironTest(FiltersTestBase):

  def testMatch(self):
    self.StartWebServer(filters.match_environ(
      'HTTP_X', r'exact', app=filters.static_page('it was ok')))

    response = self.SendRequest('/', headers={'x': 'exact'})
    self.CheckResponse(response, expected_content='it was ok')

    response = self.SendRequest('/', headers={'x': 'exact not so much'})
    self.CheckResponse(response, expected_content='it was ok')

  def testNoMatch(self):
    self.StartWebServer(filters.match_environ(
      'HTTP_X', r'None', app=filters.static_page('it was ok')))

    self.CheckError('/')
    self.CheckError('/', headers={'x': 'not a match'})

  def testMatchGroups(self):
    def application(environ, start_response):
      content = '%s %s %s' % (environ['HTTP_X.0'],
                              environ['HTTP_X.1'],
                              environ.get('HTTP_X.2') is None)
      return filters.static_page(content)(environ, start_response)

    self.StartWebServer(
      filters.match_environ('HTTP_X', '(left)-(right)', app=application))

    response = self.SendRequest('/', headers={'x': 'left-right'})
    self.CheckResponse(response, expected_content='left right True')


class MatchPathTest(FiltersTestBase):

  def testMatch(self):
    def application(environ, start_response):
      content = '%s %s' % (environ['PATH_INFO.0'],
                           environ.get('HTTP_X.1') is None)
      return filters.static_page(content)(environ, start_response)

    self.StartWebServer(filters.match_path(r'/exact([0-9]?)', app=application))

    response = self.SendRequest('/exact')
    self.CheckResponse(response, expected_content=' True')

    response = self.SendRequest('/exact1')
    self.CheckResponse(response, expected_content='1 True')

    response = self.SendRequest('/exact2')
    self.CheckResponse(response, expected_content='2 True')

  def testNoMatch(self):
    self.StartWebServer(filters.match_path('/exact'))

    self.CheckError('/', expected_code=404)
    self.CheckError('/blar', expected_code=404)
    self.CheckError('/exacta', expected_code=404)
    self.CheckError('/exact/a', expected_code=404)


if __name__ == '__main__':
  unittest.main()
