"""To test specific webapp issues."""
import os
import StringIO
import sys
import urllib
import unittest

gae_path = '/usr/local/google_appengine'

sys.path[0:0] = [
    gae_path,
    os.path.join(gae_path, 'lib', 'django_0_96'),
    os.path.join(gae_path, 'lib', 'webob'),
    os.path.join(gae_path, 'lib', 'yaml', 'lib'),
    os.path.join(gae_path, 'lib', 'protorpc'),
]

from google.appengine.ext import webapp


def add_POST(req, data):
    if data is None:
        return
    env = req.environ
    env['REQUEST_METHOD'] = 'POST'
    if hasattr(data, 'items'):
        data = data.items()
    if not isinstance(data, str):
        data = urllib.urlencode(data)
    env['wsgi.input'] = StringIO.StringIO(data)
    env['webob.is_body_seekable'] = True
    env['CONTENT_LENGTH'] = str(len(data))
    env['CONTENT_TYPE'] = 'application/octet-stream'


class TestWebapp(unittest.TestCase):
    def tearDown(self):
        webapp.WSGIApplication.active_instance = None

    def test_issue_3426(self):
        """When the content-type is 'application/x-www-form-urlencoded' and
        POST data is empty the content-type is dropped by Google appengine.
        """
        req = webapp.Request.blank('/', environ={
            'REQUEST_METHOD': 'GET',
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
        })
        self.assertEqual(req.method, 'GET')
        self.assertEqual(req.content_type, 'application/x-www-form-urlencoded')


if __name__ == '__main__':
    unittest.main()
