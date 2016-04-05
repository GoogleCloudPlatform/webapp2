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

import os
from tempfile import gettempdir


def session_lint(session):
    session.install('flake8', 'flake8-import-order')
    session.run(
        'flake8',
        '--import-order-style=google',
        'webapp2.py', 'webapp2_extras', 'tests', 'example')


def run_tests(session, requirements):
    tmpdir = gettempdir()
    session.interpreter = 'python2.7'
    session.install(
        'git+https://github.com/GoogleCloudPlatform/python-repo-tools')
    session.install('-r', requirements)
    session.install('-e', '.')
    session.run('gcprepotools', 'download-appengine-sdk', tmpdir)
    session.env['PYTHONPATH'] = os.path.join(tmpdir, 'google_appengine')
    session.run(
        'py.test',
        '--cov=webapp2',
        '--cov=webapp2_extras',
        *(['tests'] or session.posargs))


def session_tests(session):
    run_tests(session, 'requirements-dev.txt')


def session_tests_gaesdk(session):
    """Runs tests using GAE sdk versions of libraries."""
    run_tests(session, 'requirements-dev-gaesdk.txt')


def session_docs(session):
    tmpdir = gettempdir()
    session.interpreter = 'python2.7'
    session.install(
        'git+https://github.com/GoogleCloudPlatform/python-repo-tools')
    session.install('-r', 'requirements-dev.txt')
    session.install('sphinx')
    session.install('-e', '.')
    session.run('gcprepotools', 'download-appengine-sdk', tmpdir)
    session.env['PYTHONPATH'] = os.path.join(tmpdir, 'google_appengine')
    session.chdir('docs')
    session.run('make', 'html')
