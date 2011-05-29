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
with several optional utilities: sessions, internationalization, domain and
subdomain routing, configuration system, secure cookies and support for
threaded environments.

webapp2 can even be used outside of Google App Engine, independently of the
App Engine SDK.

For a complete description of how webapp2 improves webapp, see :ref:`features`.


Quick links
-----------
- `Download <http://code.google.com/p/webapp-improved/downloads/list>`_
- `Google Code repository <http://code.google.com/p/webapp-improved/>`_


Tutorials
---------
.. toctree::
   :maxdepth: 3

   tutorials/gettingstarted/index.rst


Guide
-----
.. toctree::
   :maxdepth: 3

   guide/handlers.rst
   guide/routing.rst
   guide/request.rst
   guide/response.rst
   guide/exceptions.rst


API Reference - webapp2
-----------------------
.. toctree::
   :maxdepth: 3

   api/webapp2.rst

API Reference - webapp2_extras
------------------------------
.. toctree::
   :maxdepth: 3

   api/extras.config.rst
   api/extras.i18n.rst
   api/extras.jinja2.rst
   api/extras.json.rst
   api/extras.local.rst
   api/extras.routes.rst
   api/extras.securecookie.rst
   api/extras.sessions.rst
   api/extras.sessions_memcache.rst
   api/extras.sessions_ndb.rst
   api/extras.users.rst


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
