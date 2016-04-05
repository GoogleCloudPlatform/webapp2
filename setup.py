# -*- coding: utf-8 -*-
"""
webapp2
=======
`webapp2`_ is a lightweight Python web framework compatible with Google App
Engine's `webapp`_.

webapp2 is simple. it follows the simplicity of webapp, but
improves it in some ways: it adds better URI routing and exception handling,
a full featured response object and a more flexible dispatching mechanism.

webapp2 also offers the package `webapp2_extras`_ with several optional
utilities: sessions, localization, internationalization, domain and subdomain
routing, secure cookies and others.

webapp2 can also be used outside of Google App Engine, independently of the
App Engine SDK.

For a complete description of how webapp2 improves webapp, see
`webapp2 features`_.

Quick links
-----------

- `User Guide <https://webapp2.readthedocs.org/>`_
- `Repository <https://github.com/GoogleCloudPlatform/webapp2>`_
- `Discussion Group <https://groups.google.com/forum/#!forum/webapp2>`_
- `@webapp2 <https://twitter.com/#!/webapp2>`_

.. _webapp: http://code.google.com/appengine/docs/python/tools/webapp/
.. _webapp2: https://github.com/GoogleCloudPlatform/webapp2
.. _webapp2_extras: https://webapp2.readthedocs.org/#api-reference-webapp2-extras
.. _webapp2 features: https://webapp2.readthedocs.org/features.html
"""
from setuptools import setup

setup(
    name='webapp2',
    version='2.5.2',
    license='Apache Software License',
    url='http://webapp-improved.appspot.com',
    description="Taking Google App Engine's webapp to the next level!",
    long_description=__doc__,
    author='The Webapp2 Maintainers',
    author_email='webapp2-maintainers@googlegroups.com',
    zip_safe=False,
    platforms='any',
    py_modules=[
        'webapp2',
    ],
    packages=[
        'webapp2_extras',
        'webapp2_extras.appengine',
        'webapp2_extras.appengine.auth',
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
