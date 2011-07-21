.. _api.extras.mako:

Mako
====
.. module:: webapp2_extras.mako

This module provides Mako template support for webapp2.

To use it, you must include the ``mako`` package inside your application
directory (for App Engine) or install it in your virtual environment
(for other servers).

You can download ``mako`` from PyPi:

    http://pypi.python.org/pypi/Mako

Learn more about Mako:

    http://www.makotemplates.org/

.. autodata:: default_config

.. autoclass:: Mako
   :members: __init__, render_template

.. autofunction:: get_mako
.. autofunction:: set_mako
