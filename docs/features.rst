.. _features:

webapp2 features
================
Here's an overview of the main improvements of webapp2 compared to webapp.

.. contents:: Table of Contents
   :depth: 3
   :backlinks: none

Extreme compatibility
---------------------
webapp2 is designed to work with existing webapp apps without any changes.
See how this looks familiar::

    import webapp2 as webapp
    from google.appengine.ext.webapp.util import run_wsgi_app

    class HelloWorldHandler(webapp.RequestHandler):
        def get(self):
            self.response.out.write('Hello, World!')

    app = webapp.WSGIApplication([
        ('/', HelloWorldHandler),
    ], debug=True)

    def main():
        run_wsgi_app(app)

    if __name__ == '__main__':
        main()

``RequestHandler``, ``Request``, ``Response`` and ``WSGIApplicationm`` classes
are compatible with the webapp API. Migrationg from webapp is intended to
be a breeze.

Full-featured Response object
-----------------------------
webapp2 uses a full-featured Response object from ``WebOb``. If offers several
conveniences to set headers, like easy cookies and other goodies::

    class MyHandler(webapp2.RequestHandler):
        def get(self):
            self.response.set_cookie('key', 'value', max_age=360, path='/')

Improved exception handling
---------------------------
Improved exception handling in many ways. For example, app-wide exception
handlers can also be set::

    def handle_404(request, response):
        response.write('Oops! I could swear this page was here!')
        response.set_status(404)

    app = webapp2.WSGIApplication([
        ('/', MyHandler),
    ])
    app.error_handlers[404] = handle_404


Status code exceptions
----------------------
``abort()`` (or ``self.abort()`` inside handlers) raises a proper
``HTTPException`` (from ``WebOb``) and stops processing::

    # Raise a 'Not Found' exception and let the 404 error handler do its job.
    abort(404)
    # Raise a 'Forbidden' exception and let the 403 error handler do its job.
    self.abort(403)

Lazy handlers
-------------
Lazy handlers are defined as a string to be imported only when needed::

    app = webapp2.WSGIApplication([
        ('/', 'my.module.MyHandler'),
    ])

Keyword arguments from URI
--------------------------
``RequestHandler`` methods can also receive keyword arguments, which are easier
to maintain than positional ones. Simply use the ``Route`` class to define
URIs (and you can also create custom route classes, examples
`here <http://code.google.com/p/webapp-improved/source/browse/webapp2_extras/routes.py>`_)::

    class BlogArchiveHandler(webapp2.RequestHandler):
        def get(self, year=None, month=None):
            self.response.write('Hello, keyword arguments world!')

    app = webapp2.WSGIApplication([
        webapp2.Route('/<year:\d{4}>/<month:\d{2}>', BlogArchiveHandler, 'blog-archive'),
    ])

URI Routing fully compatible with webapp's
------------------------------------------
Positional arguments are also supported, like in webapp::

    class BlogArchiveHandler(webapp2.RequestHandler):
        def get(self, year, month):
            self.response.write('Hello, webapp routing world!')

    app = webapp2.WSGIApplication([
        ('/(\d{4})/(\d{2})', BlogArchiveHandler),
    ])

Custom handler methods
----------------------
webapp2 routing and dispatching system can do a lot more than webapp.
For example, handlers can also use custom methods::

    class MyHandler(webapp2.RequestHandler):
        def my_custom_method(self):
            self.response.write('Hello, custom method world!')

        def my_other_method(self):
            self.response.write('Hello, another custom method world!')

    app = webapp2.WSGIApplication([
        webapp2.Route('/', handler=MyHandler, name='custom-1', handler_method='my_custom_method'),
        webapp2.Route('/other', handler=MyHandler, name='custom-2', handler_method='my_other_method'),
    ])

View functions
--------------
Handlers don't need to be classes. For those that prefer, functions can be used
as well::

    def my_sweet_function(request, response):
        response.write('Hello, function world!')

    app = webapp2.WSGIApplication([
        webapp2.Route('/', handler=my_sweet_function, name='home'),
    ])

More flexible dispatching mechanism
-----------------------------------
The ``WSGIApplication`` in webapp is a hard to extend. It dispatches the
handler giving little chance and extend how it is done, or to pre-process
requests before a handler method is actually called. In webapp2, the handlers
dispatch themselves, making it easy to implement before and after dispatch
hooks.

webapp2 is thought to be lightweight but flexible. It basically provides an
easy to extend URI routing and dispatching mechanisms.

URI builder
-----------
URIs from routes can be built. THis is more maintanable than hardocding them
in the code or templates. Simply use the ``uri_for()`` method inside a
handler::

    url = self.uri_for('blog-archive', year='2010', month='07')

And a helper for redirects builds the URI to redirect to.
redirect_to = redirect + uri_for::

    self.redirect_to('blog-archive', year='2010', month='07')

Redirection for legacy URIs
---------------------------
Old URIs can be conveniently redirected using a simple route::

    def get_redirect_url(handler, *args, **kwargs):
        return handler.url_for('view', item=kwargs.get('item'))

    app = webapp2.WSGIApplication([
        webapp2.Route('/view/<item>', ViewHandler, 'view'),
        webapp2.Route('/old-page', RedirectHandler, defaults={'url': '/view/i-came-from-a-redirect'}),
        webapp2.Route('/old-view/<item>', RedirectHandler, defaults={'url': get_redirect_url}),
    ])

single file, well-tested and documented
---------------------------------------
webapp2 is an extensively documented `single file <http://code.google.com/p/webapp-improved/source/browse/webapp2/__init__.py>`_
and has almost 100% test coverage and . The source code is explicit, magic-free
and made to be extended. We like less.

Fast, fast, fast
----------------
webapp2 makes a lot of improvements but keeps same performance as webapp.
Here are some start times and consumed CPU for a cold start:

.. code-block:: text

   100ms 77cpu_ms
   143ms 58cpu_ms
   155ms 77cpu_ms
   197ms 96cpu_ms
   106ms 77cpu_ms

Extras
------
The `webapp2_extras <http://code.google.com/p/webapp-improved/source/browse/#hg%2Fwebapp2_extras>`_
package provides common utilities that integrate well with webapp2:

- Configuration system
- Localization and internationalization support
- Sessions using secure cookies, memcache or datastore
- Extra route classes -- to match subdomains and other conveniences
- Support for third party libraries: Jinja2 and Google's ProtoRPC
- Support for threaded environments, so that you can use webapp2 outside of
  App Engine
