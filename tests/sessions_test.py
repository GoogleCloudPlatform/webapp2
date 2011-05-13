# -*- coding: utf-8 -*-
import webapp2
from webapp2_extras import config as webapp2_config
from webapp2_extras import sessions

import test_base


class App(object):
    @property
    def config(self):
        config = sessions.default_config.copy()
        config['secret_key'] = 'my-super-secret'
        return {'webapp2_extras.sessions': config}

app = App()


class TestSecureCookieSession(test_base.BaseTestCase):
    factory = sessions.SecureCookieSessionFactory

    def test_get_save_session(self):

        # Round 1 -------------------------------------------------------------

        req = webapp2.Request.blank('/')
        req.app = app
        store = sessions.SessionStore(req)

        session = store.get_session(factory=self.factory)
        session['a'] = 'b'
        session['c'] = 'd'
        session['e'] = 'f'

        rsp = webapp2.Response()
        store.save_sessions(rsp)

        # Round 2 -------------------------------------------------------------

        cookies = rsp.headers.get('Set-Cookie')
        req = webapp2.Request.blank('/', headers=[('Cookie', cookies)])
        req.app = app
        store = sessions.SessionStore(req)

        session = store.get_session(factory=self.factory)
        self.assertEqual(session['a'], 'b')
        self.assertEqual(session['c'], 'd')
        self.assertEqual(session['e'], 'f')

        session['g'] = 'h'

        rsp = webapp2.Response()
        store.save_sessions(rsp)

        # Round 3 -------------------------------------------------------------

        cookies = rsp.headers.get('Set-Cookie')
        req = webapp2.Request.blank('/', headers=[('Cookie', cookies)])
        req.app = app
        store = sessions.SessionStore(req)

        session = store.get_session(factory=self.factory)
        self.assertEqual(session['a'], 'b')
        self.assertEqual(session['c'], 'd')
        self.assertEqual(session['e'], 'f')
        self.assertEqual(session['g'], 'h')

    def test_flashes(self):

        # Round 1 -------------------------------------------------------------

        req = webapp2.Request.blank('/')
        req.app = app
        store = sessions.SessionStore(req)

        session = store.get_session(factory=self.factory)
        flashes = session.get_flashes()
        self.assertEqual(flashes, [])
        session.add_flash('foo')

        rsp = webapp2.Response()
        store.save_sessions(rsp)

        # Round 2 -------------------------------------------------------------

        cookies = rsp.headers.get('Set-Cookie')
        req = webapp2.Request.blank('/', headers=[('Cookie', cookies)])
        req.app = app
        store = sessions.SessionStore(req)

        session = store.get_session(factory=self.factory)

        flashes = session.get_flashes()
        self.assertEqual(flashes, [[u'foo', None]])

        flashes = session.get_flashes()
        self.assertEqual(flashes, [])

        session.add_flash('bar')
        session.add_flash('baz', 'important')

        rsp = webapp2.Response()
        store.save_sessions(rsp)

        # Round 3 -------------------------------------------------------------

        cookies = rsp.headers.get('Set-Cookie')
        req = webapp2.Request.blank('/', headers=[('Cookie', cookies)])
        req.app = app
        store = sessions.SessionStore(req)

        session = store.get_session(factory=self.factory)

        flashes = session.get_flashes()
        self.assertEqual(flashes, [[u'bar', None], [u'baz', 'important']])

        flashes = session.get_flashes()
        self.assertEqual(flashes, [])


if __name__ == '__main__':
    test_base.main()
