import os
from tempfile import gettempdir


def session_lint(session):
    session.install('flake8', 'flake8-import-order')
    session.run(
        'flake8',
        '--import-order-style=google',
        'webapp2.py', 'webapp2_extras', 'tests', 'example')


def session_tests(session):
    tmpdir = gettempdir()
    session.interpreter = 'python2.7'
    session.install(
        'git+https://github.com/GoogleCloudPlatform/python-repo-tools')
    session.install('-r', 'requirements-dev.txt')
    session.install('-e', '.')
    session.run('gcprepotools', 'download-appengine-sdk', tmpdir)
    session.env['PYTHONPATH'] = os.path.join(tmpdir, 'google_appengine')
    session.run('py.test', *(['tests'] or session.posargs))


def session_docs(session):
    tmpdir = gettempdir()
    session.interpreter = 'python2.7'
    session.install(
        'git+https://github.com/GoogleCloudPlatform/python-repo-tools')
    session.install('-r', 'requirements-dev.txt')
    session.install('sphinx')
    session.run('gcprepotools', 'download-appengine-sdk', tmpdir)
    session.env['PYTHONPATH'] = os.path.join(tmpdir, 'google_appengine')
    session.chdir('docs')
    session.run('make', 'html')
