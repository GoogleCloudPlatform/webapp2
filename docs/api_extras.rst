.. _contents:

webapp2_extras
==============
The webapp2_extras package provides common utilities that integrate well with
`webapp2 <http://code.google.com/p/webapp-improved/>`_.

.. contents:: Table of Contents
   :depth: 3
   :backlinks: none

Some webapp2_extras modules are not listed here yet but will be soon:

- `i18n <http://code.google.com/p/webapp-improved/source/browse/webapp2_extras/i18n.py>`_ (localization and internationalization support)
- `jinja2 <http://code.google.com/p/webapp-improved/source/browse/webapp2_extras/jinja2.py>`_ (Jinja2 support)
- `local <http://code.google.com/p/webapp-improved/source/browse/webapp2_extras/local.py>`_ (support for threaded environments -- for non-GAE servers)
- `protorpc <http://code.google.com/p/webapp-improved/source/browse/webapp2_extras/protorpc.py>`_ (support for `ProtoRPC <http://code.google.com/p/google-protorpc/>`_)
- `routes <http://code.google.com/p/webapp-improved/source/browse/webapp2_extras/routes.py>`_ (extra route classes -- to match subdomains and other conveniences)


Configuration
-------------
.. module:: webapp2_extras.config
.. autoclass:: Config
   :members: loaded, __init__, __setitem__, update, setdefault, get,
             get_config


JSON
----
.. module:: webapp2_extras.json

.. autofunction:: encode

.. autofunction:: decode

.. autofunction:: b64encode

.. autofunction:: b64decode

.. autofunction:: quote

.. autofunction:: unquote


Secure Cookies
--------------
.. module:: webapp2_extras.securecookie

.. autoclass:: SecureCookieSerializer
   :members: __init__, serialize, deserialize


Sessions
--------
.. module:: webapp2_extras.sessions

.. autodata:: default_config

.. autoclass:: SessionStore
   :members: __init__, get_session, get_secure_cookie, set_secure_cookie,
             save_sessions

.. autoclass:: SessionDict
   :members: get_flashes, add_flash

Secure cookie sessions
~~~~~~~~~~~~~~~~~~~~~~
.. autoclass:: SecureCookieSessionFactory

Datastore sessions
~~~~~~~~~~~~~~~~~~
.. module:: webapp2_extras.sessions_ndb

.. autoclass:: DatastoreSessionFactory

Memcache sessions
~~~~~~~~~~~~~~~~~
.. module:: webapp2_extras.sessions_memcache

.. autoclass:: MemcacheSessionFactory


.. _Tornado: http://www.tornadoweb.org/
