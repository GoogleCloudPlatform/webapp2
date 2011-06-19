.. _tutorials.quickstart.nogae:

Quick start (to use webapp2 outside of App Engine)
==================================================
webapp2 can also be used outside of App Engine as a general purpose web
framework, as it offers these features:

- It is independent of the App Engine SDK. If the SDK is not found, it sets
  fallbacks to be used outside of GAE.
- It supports threaded environments, using the :ref:`api.extras.local_app`
  module.
- All webapp2_extras modules are designed to be thread-safe.
- It is compatible with ``WebOb`` 1.0 and superior, which fixes several bugs
  found in the version bundled with the SDK (which is of course supported as
  well).

It won't support App Engine services, but if you like webapp, why not use it
as a WSGI framework ouside of GAE as well? Here we'll describe how to do this.

Here we will describe how to use webapp2 outside of App Engine. If you want to
use on App Engine, you should read the :ref:`tutorials.quickstart` tutorial.


Install a distutils library
---------------------------
If you don't have a distutils library (`distribute <http://pypi.python.org/pypi/distribute>`_
or `setuptools <http://pypi.python.org/pypi/setuptools>`_) installed on
you system yet, you need to install one. Distribute is recommended, but
setuptools will serve as well.

Distribute is "the standard method for working with Python module
distributions". It will manage our package dependencies and upgrades.
If you already have one of them, jump to next step. If not, the installation
is straighforward:

**1.** Download the installer and save it anywhere. It is a single file:

    http://python-distribute.org/distribute_setup.py

**2.** Execute it using your Python executable (this will require sudo if
you are using Linux of a Mac):

.. code-block:: text

   $ python distribute_setup.py

If you don't see any error messages, yay, it installed successfully. Let's
move forward. For Windows, check the distribute or setuptools documentation.


Install a package installer
---------------------------
We need a package installer (``pip`` or ``easy_install``) to install and
update our libraries. Both will work, but if you don't have any yet, ``pip``
is recommended. If you already have one of them, jump to next step. If not
let's install it:

**1.** Call easy_install to install it using your Python executable (this
will require sudo if you are using Linux of a Mac):

.. code-block:: text

   $ easy_install pip

That's it. If no errors appear, we are good to go.


Create a directory for your app
-------------------------------
Create a directory ``hellowebapp2`` for your new app. It is where you will
setup the environment and create your application.


Install virtualenv
------------------
Install `virtualenv <http://pypi.python.org/pypi/virtualenv>`_, which sets a
"virtual environment" that allows you to run different projects with separate
libraries side by side. This is a good idea both for development and
production, as it'll assure that each project uses their own library versions
and don't affect each other.

**1.** To install it on a Linux or Mac systems, type in the command line:

.. code-block:: text

   $ sudo pip install virtualenv

Or, using easy_install:

.. code-block:: text

   $ sudo easy_install virtualenv

**2.** Then access your ``hellowebapp2`` and create the virtual environment
with the following command:

.. code-block:: text

   $ virtualenv env

**3.** Activate the environment. On Linux of Mac, use:

.. code-block:: text

   $ . env/bin/activate

Or on a Windows system:

.. code-block:: text

   $ env\scripts\activate


Install WebOb, Paste and webapp2
--------------------------------
We need three libraries to use webapp2: `WebOb <http://pypi.python.org/pypi/WebOb>`_, for Request and Response objects,
`Paste <http://pypi.python.org/pypi/Paste>`_, for the development server,
and `webapp2 <http://pypi.python.org/pypi/webapp2>`_ itself. Type this to
install them using the activated environment from the previous step:

.. code-block:: text

   $ pip install WebOb
   $ pip install Paste
   $ pip install webapp2

Or, using easy_install:

.. code-block:: text

   $ easy_install WebOb
   $ easy_install Paste
   $ easy_install webapp2

Now the environment is ready for your first app.


Hello, webapp2!
---------------
Create a file ``main.py`` inside your ``hellowebapp2`` directory and define
a handler to display a 'Hello, webapp2!' message. This will be our bootstrap
file::

    import webapp2
    from webapp2_extras import local_app

    class HelloWebapp2(webapp2.RequestHandler):
        def get(self):
            self.response.write('Hello, webapp2!')

    app = local_app.WSGIApplication([
        ('/', HelloWebapp2),
    ], debug=True)

    def main():
        from paste import httpserver
        httpserver.serve(app, host='127.0.0.1', port='8080')

    if __name__ == '__main__':
        main()

Notice that we use ``local_app.WSGIApplication``. This is a special version
of the WSGI application that is thread-safe.


Test your app
-------------
Now start the development server using the Python executable provided by
virtualenv:

.. code-block:: text

   $ python main.py

The web server is now running, listening for requests on port 8080. You can
test the application by visiting the following URL in your web browser:

    http://127.0.0.1:8080/
