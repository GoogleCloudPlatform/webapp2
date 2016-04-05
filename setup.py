# Copyright 2016 webapp2 AUTHORS.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from codecs import open

from setuptools import setup


long_description = open('README.rst', 'r', encoding='utf-8').read()


setup(
    name='webapp2',
    version='3.0.0',
    license='Apache Software License',
    url='http://webapp2.readthedocs.org',
    description="Taking Google App Engine's webapp to the next level!",
    long_description=long_description,
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
