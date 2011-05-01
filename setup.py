# -*- coding: utf-8 -*-
"""
webapp2
~~~~~~~

This is an attempt to improve Google App Engine's
`webapp <http://code.google.com/appengine/docs/python/tools/webapp/>`_
framework keeping maximum compatibility and same performance.

Features overview: http://code.google.com/p/webapp-improved/
"""
from setuptools import setup

setup(
    name = 'webapp2',
    version = '1.0',
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