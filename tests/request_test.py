# -*- coding: utf-8 -*-
import webapp2

import test_base


class TestResponse(test_base.BaseTestCase):
    def test_get(self):
        req = webapp2.Request.blank('/?1=2&1=3&3=4', POST='5=6&7=8')

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
        req = webapp2.Request.blank('/?1=2&3=4', POST='5=6&7=8')

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