# -*- coding: utf-8 -*-
"""
webapp2
~~~~~~~

Google App Engine's `webapp`_ is awesome:

- It is clean and simple enough.
- Not many arbitrary decisions taken.
- Not many rules to learn.
- Not many walls to hit.
- No room for WTF moments.
- It is fast. Fast. Very fast.


.. _webapp: http://code.google.com/appengine/docs/python/tools/webapp/

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