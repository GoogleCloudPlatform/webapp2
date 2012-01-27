"""
gae-pytz
========
pytz has a severe performance problem that impedes its usage on Google App
Engine. This is caused because pytz.__init__ builds a list of available
zoneinfos checking the entire zoneinfo database (which means: it tries to open
hundreds of files). This is done in the module globals, so it is not easily
avoidable. And it is far from ideal to do this in App Engine - app
initialization becomes unacceptable if every time we import pytz it checks
500+ files.

In this alternative version, pytz is highly optimized for App Engine, following
ideas from several recipes around:

- database files are not automatically reads when the module is imported
- the database files are loaded using zipimport to reduce number of files
- it uses memcache to cache already loaded zoneinfos

This results in almost unnoticeable load time and makes pytz usable on App
Engine.
"""
from setuptools import setup, find_packages


setup(
    name='gaepytz',
    version='2011h',
    url='http://code.google.com/p/gae-pytz/',
    license='MIT',
    author='Rodrigo Moraes',
    author_email='rodrigo.moraes@gmail.com',
    description='A version of pytz that works well on Google App Engine.',
    long_description=__doc__,
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages=['pytz'],
    include_package_data=True,
    package_data={'': ['*.zip']},
)
