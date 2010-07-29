# -*- coding: utf-8 -*-
"""
webapp2
~~~~~~~

Taking webapp to the next level! Here are the key features:

- ``Request` and ``Response`` objects fully compatible with `webapp.Request`
  and `webapp.Response`.

- ``RequestHandler`` object mostly compatible with ``webapp.RequestHandler``:
  - Handler methods receive keyword arguments instead of positional ones.
  - initialize() is replaced by a proper ``__init__()``.
  - Everything else is implemented in the same way.

- Keyword based URLs:

  .. code-block:: python

     class BlogPostHandler(RequestHandler):
         def get(self, year=None, month=None, slug=None):
             # Yay, URL arguments are passed as keywords!
             pass

     app = WSGIApplication([
         ('/{year:\d\d\d\d}/{month:\d\d}/{slug}', BlogPostHandler, 'blog-item'),
     ]

- Fully reversible URLs:

  .. code-block:: python

     url = self.url_for('blog-item', year=2010, month=8, slug='hello')

- Automatic redirect for legacy URLs:

  .. code-block:: python

     app = WSGIApplication([
         ('/old-url', RedirectHandler, 'legacy-url', {'url': '/new-url'}),
     ])

- Lazy handlers:

.. code-block:: python

     app = WSGIApplication([
         ('/', 'my.module.MyHandler'),
     ]

- Handler dispatching: the handler dispatches the current method,
  allowing before and after dispatch hooks in a *per-handler* basis.
  This opens the door for ``RequestHandler`` plugins:

  .. code-block:: python

     class SessionPlugin(object):
         def before_dispatch(self, handler):
             # Initialize session...
             pass

         def after_dispatch(self, handler):
             # Save session...
             pass

     sessions = SessionPlugin()

     class BlogPostHandler(RequestHandler):
         plugins = [sessions]

         def get(self, year=None, month=None, slug=None):
             # Sessions are available!
             pass

- Uses webob.Response:

  - Easy to set cookies.
  - Easy headers.
  - Several helpers such as conditional responses with automatic ETag
    checking.
  - etc.

  .. code-block:: python

     self.response.set_cookie('key', 'value', max_age=360)

Based on `webapp`_ with some functions and ideas borrowed from `WebOb`_
and `Tornado`_.

.. _webapp: http://code.google.com/appengine/docs/python/tools/webapp/
.. _WebOb: http://pythonpaste.org/webob/
.. _Tornado: http://www.tornadoweb.org/
.. _Another Do-It-Yourself Framework: http://pythonpaste.org/webob/do-it-yourself.html
"""
from setuptools import setup

setup(
    name = 'webapp2',
    version = '0.1',
    license = 'Apache Software License',
    url = 'http://www.tipfy.org/',
    description = "Taking Google App Engine's webapp to the next level!",
    long_description = __doc__,
    author = 'Rodrigo Moraes',
    author_email = 'rodrigo.moraes@gmail.com',
    zip_safe = False,
    platforms = 'any',
    packages = [
        'webapp2',
    ],
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)