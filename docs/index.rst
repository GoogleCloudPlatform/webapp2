.. webapp2 documentation master file, created by
   sphinx-quickstart on Sat Jul 31 10:41:37 2010.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to webapp2!
===================
`webapp2 <http://code.google.com/p/webapp-improved/>`_ is a lightweight Python
web framework compatible with Google App Engine's
`webapp <http://code.google.com/appengine/docs/python/tools/webapp/>`_.

webapp2 is a `single file <http://code.google.com/p/webapp-improved/source/browse/webapp2.py>`_
that follows the simplicity of webapp, but improves it in some ways: it extends
webapp to offer better URI routing and exception handling, a full featured
response object and a more flexible dispatching mechanism.

webapp2 also offers the package `webapp2_extras <http://code.google.com/p/webapp-improved/source/browse/#hg%2Fwebapp2_extras>`_
with several optional utilities: sessions, localization, internationalization,
domain and subdomain routing, secure cookies and support for threaded
environments.

webapp2 can also be used outside of Google App Engine, independently of the
App Engine SDK.

For a complete description of how webapp2 improves webapp, see :ref:`features`.


Quick links
-----------
- `Downloads <http://code.google.com/p/webapp-improved/downloads/list>`_
- `Google Code Repository <http://code.google.com/p/webapp-improved/>`_
- `Discussion Group <http://groups.google.com/group/webapp2>`_
- `Documentation PDF <http://webapp-improved.googlecode.com/files/webapp2-2.0.2.pdf>`_

.. `Samples for Google App Engine <http://code.google.com/p/google-app-engine-samples/>`_:
   several mini-apps for webapp that serve as examples (they should work with
   webapp2 too).


Tutorials
---------
.. toctree::
   :maxdepth: 1

   tutorials/quickstart.rst
   tutorials/quickstart.nogae.rst
   tutorials/gettingstarted/index.rst
   tutorials/i18n.rst


Guide
-----
.. toctree::
   :maxdepth: 3

   guide/app.rst
   guide/routing.rst
   guide/handlers.rst
   guide/request.rst
   guide/response.rst
   guide/exceptions.rst
   guide/testing.rst
   guide/extras.rst


API Reference - webapp2
-----------------------
.. toctree::
   :maxdepth: 2

   api/webapp2.rst

API Reference - webapp2_extras
------------------------------
.. toctree::
   :maxdepth: 1

   api/webapp2_extras/i18n.rst
   api/webapp2_extras/jinja2.rst
   api/webapp2_extras/json.rst
   api/webapp2_extras/local.rst
   api/webapp2_extras/mako.rst
   api/webapp2_extras/protorpc.rst
   api/webapp2_extras/routes.rst
   api/webapp2_extras/securecookie.rst
   api/webapp2_extras/security.rst
   api/webapp2_extras/sessions.rst

API Reference - webapp2_extras.appengine
----------------------------------------
App Engine-specific modules.

.. toctree::
   :maxdepth: 1

   api/webapp2_extras/appengine/sessions_memcache.rst
   api/webapp2_extras/appengine/sessions_ndb.rst
   api/webapp2_extras/appengine/users.rst

Indices and tables
------------------
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Credits
-------
Because webapp2 is intended to be compatible with webapp, the official webapp
documentation is valid for webapp2 too. Parts of this documentation were ported
from `the official documentation for App Engine/Python <http://code.google.com/appengine/docs/python/>`_,
written by the App Engine team and licensed under the Creative Commons
Attribution 3.0 License.

webapp2 has code ported from `Werkzeug <http://werkzeug.pocoo.org/>`_ and
`Tipfy <http://www.tipfy.org/>`_.

webapp2_extras has code ported from Werkzeug, Tipfy and
`Tornado Web Server <http://www.tornadoweb.org/>`_.

The `Sphinx <http://sphinx.pocoo.org/>`_ theme mimics the
`App Engine official documentation <http://code.google.com/appengine/docs/>`_.

This library was not created and is not maintained by Google.


Contribute
----------
webapp2 is considered stable, feature complete and well tested, but if you
think something is missing or is not working well, please describe it in our
issue tracker:

    http://code.google.com/p/webapp-improved/issues/list

Let us know if you found a bug or if something can be improved. New tutorials
or webapp2_extras modules are welcome, and tests or documentation are never
too much.

Thanks!


License
-------
webapp2 is licensed under the
`Apache License 2.0 <http://www.apache.org/licenses/LICENSE-2.0>`_.
