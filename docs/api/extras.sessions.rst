.. _api.extras.sessions:

Sessions
========
.. module:: webapp2_extras.sessions

.. autodata:: default_config

.. autoclass:: SessionStore
   :members: __init__, get_session, get_secure_cookie,
             set_secure_cookie, save_sessions, save_secure_cookie

.. autoclass:: SessionDict
   :members: get_flashes, add_flash

.. autoclass:: SecureCookieSessionFactory

.. autofunction:: get_store
.. autofunction:: set_store
