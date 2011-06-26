# -*- coding: utf-8 -*-
import StringIO

import webapp2

import test_base

def _norm_req(s):
    return '\r\n'.join(s.strip().replace('\r','').split('\n'))
_test_req = """
POST /webob/ HTTP/1.0
Accept: */*
Cache-Control: max-age=0
Content-Type: multipart/form-data; boundary=----------------------------deb95b63e42a
Host: pythonpaste.org
User-Agent: UserAgent/1.0 (identifier-version) library/7.0 otherlibrary/0.8

------------------------------deb95b63e42a
Content-Disposition: form-data; name="foo"

foo
------------------------------deb95b63e42a
Content-Disposition: form-data; name="bar"; filename="bar.txt"
Content-type: application/octet-stream

these are the contents of the file 'bar.txt'

------------------------------deb95b63e42a--
"""

_test_req2 = """
POST / HTTP/1.0
Content-Length: 0

"""

_test_req = _norm_req(_test_req)
_test_req2 = _norm_req(_test_req2) + '\r\n'


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
    env['CONTENT_TYPE'] = 'application/x-www-form-urlencoded'


class TestRequest(test_base.BaseTestCase):
    def test_get(self):
        req = webapp2.Request.blank('/?1=2&1=3&3=4')
        add_POST(req, '5=6&7=8')

        res = req.get('1')
        self.assertEqual(res, '2')

        res = req.get('1', allow_multiple=True)
        self.assertEqual(res, ['2', '3'])

        res = req.get('8')
        self.assertEqual(res, '')

        res = req.get('8', allow_multiple=True)
        self.assertEqual(res, [])

        res = req.get('8', default_value='9')
        self.assertEqual(res, '9')

    def test_get_with_FieldStorage(self):
        # A valid request without a Content-Length header should still read
        # the full body.
        # Also test parity between as_string and from_string / from_file.
        import cgi
        req = webapp2.Request.from_string(_test_req)
        self.assertTrue(isinstance(req, webapp2.Request))
        self.assertTrue(not repr(req).endswith('(invalid WSGI environ)>'))
        self.assertTrue('\n' not in req.http_version or '\r' in req.http_version)
        self.assertTrue(',' not in req.host)
        self.assertTrue(req.content_length is not None)
        self.assertEqual(req.content_length, 337)
        self.assertTrue('foo' in req.body)
        bar_contents = "these are the contents of the file 'bar.txt'\r\n"
        self.assertTrue(bar_contents in req.body)
        self.assertEqual(req.params['foo'], 'foo')
        bar = req.params['bar']
        self.assertTrue(isinstance(bar, cgi.FieldStorage))
        self.assertEqual(bar.type, 'application/octet-stream')
        bar.file.seek(0)
        self.assertEqual(bar.file.read(), bar_contents)

        bar = req.get_all('bar')
        self.assertEqual(bar[0], bar_contents)

        # out should equal contents, except for the Content-Length header,
        # so insert that.
        _test_req_copy = _test_req.replace('Content-Type',
                            'Content-Length: 337\r\nContent-Type')
        self.assertEqual(str(req), _test_req_copy)

        req2 = webapp2.Request.from_string(_test_req2)
        self.assertTrue('host' not in req2.headers)
        self.assertEqual(str(req2), _test_req2.rstrip())
        self.assertRaises(ValueError,
                          webapp2.Request.from_string, _test_req2 + 'xx')

    def test_get_with_POST(self):
        req = webapp2.Request.blank('/?1=2&1=3&3=4', POST={5: 6, 7: 8},
                                    unicode_errors='ignore')

        res = req.get('1')
        self.assertEqual(res, '2')

        res = req.get('1', allow_multiple=True)
        self.assertEqual(res, ['2', '3'])

        res = req.get('8')
        self.assertEqual(res, '')

        res = req.get('8', allow_multiple=True)
        self.assertEqual(res, [])

        res = req.get('8', default_value='9')
        self.assertEqual(res, '9')

    def test_arguments(self):
        req = webapp2.Request.blank('/?1=2&3=4')
        add_POST(req, '5=6&7=8')

        res = req.arguments()
        self.assertEqual(res, ['1', '3', '5', '7'])

    def test_get_range(self):
        req = webapp2.Request.blank('/')
        res = req.get_range('1', min_value=None, max_value=None, default=None)
        self.assertEqual(res, None)

        req = webapp2.Request.blank('/?1=2')
        res = req.get_range('1', min_value=None, max_value=None, default=0)
        self.assertEqual(res, 2)

        req = webapp2.Request.blank('/?1=foo')
        res = req.get_range('1', min_value=1, max_value=99, default=100)
        self.assertEqual(res, 99)


if __name__ == '__main__':
    test_base.main()