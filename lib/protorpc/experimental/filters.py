
import re

from protorpc import util


@util.positional(1)
def static_page(content='',
                status='200 OK',
                content_type='text/html',
                headers=None):
  if not isinstance(status, basestring):
    status = '%d %s' % tuple(status)

  if isinstance(headers, dict):
    headers = headers.iteritems()

  headers = [('content-length', str(len(content))),
             ('content-type', content_type),
            ] + list(headers or [])

  def static_page_application(environ, start_response):
    start_response(status, headers)
    yield content

  return static_page_application


HTTP_OK = static_page()
HTTP_BAD_REQUEST = static_page(status=(400, 'Bad Request'))
HTTP_UNAUTHORIZED = static_page(status=(401, 'Unauthorized'))
HTTP_NOT_FOUND = static_page(status=(404, 'Not Found'))

PROTOCOLS_ENVIRON = 'protorpc.protocols'


def filter_request(filter, app=HTTP_OK, on_error=HTTP_BAD_REQUEST):
  def filter_request_application(environ, start_response):
    if filter(environ):
      return app(environ, start_response)
    else:
      return on_error(environ, start_response)
  return filter_request_application


def filter_environ(name, filter, **kwargs):
  def filter_environ_filter(environ):
    return filter(environ.get(name))

  return filter_request(filter_environ_filter, **kwargs)


def filter_header(name, filter, **kwargs):
  name = 'HTTP_%s' % name.upper().replace('-', '_')
  return filter_environ(name, filter, **kwargs)


def expect_header(name, **kwargs):
  def expect_header_filter(value):
    return value is not None

  return filter_header(name, expect_header_filter, **kwargs)


def set_environ(name, value, app=HTTP_OK):
  def set_environ_filter(environ):
    environ[name] = value
    return True

  return filter_request(set_environ_filter, app=app)


def use_protocols(protocols, app=HTTP_OK):
  return set_environ(PROTOCOLS_ENVIRON, protocols, app=app)


def set_header(name, value, app=HTTP_OK):
  name = 'HTTP_%s' % name.upper().replace('-', '_')
  return set_environ(name, value, app=app)


def environ_equals(name, string, **kwargs):
  return check_header(name, lambda value: value == string, **kwargs)


def match_environ(name, regex, exact=True, **kwargs):
  if isinstance(regex, basestring):
    regex = re.compile(r'%s' % regex)

  def match_environ_filter(environ):
    value = environ.get(name)
    if value is None:
      return False
    match = regex.match(str(value))
    if not match:
      return False

    for index, group in enumerate(match.groups()):
      environ['%s.%d' % (name, index)] = group
    return True

  return filter_request(match_environ_filter, **kwargs)


def match_path(path, **kwargs):
  kwargs.setdefault('on_error', HTTP_NOT_FOUND)
  if isinstance(path, basestring):
    path = r'^%s$' % path
  return match_environ('PATH_INFO', path, **kwargs)


def app_mapping(mapping, on_error=HTTP_NOT_FOUND):
  application = on_error
  for path, app in reversed(mapping):
    application = match_path(path, app=app, on_error=application)
  return application


def service_app(service_factory,
                service_path=None,
                protocols=None,
                app=HTTP_NOT_FOUND):

  def service_app_application(environ, start_response):
    pass

  application = environ_equals('REQUEST_METHOD',
                               'POST',
                               app=application
                               **kwargs)

  if service_path is None:
    service_path = '/%s' + service_class.definition_name().replace('.', '/')

  application = match_path(service_path,
                           app=application,
                           on_error=app)

  if protocols:
    set_protocols(protocols, app=application)

  return application
