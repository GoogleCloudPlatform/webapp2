.. _tutorials.quickstart:

Quickstart
==========
If you already know webapp, webapp2 is very easy to get started. You can use
webapp2 exactly like webapp, and learn the new features as you go.

If you are new to App Engine, read :ref:`tutorials.gettingstarted.index` first.


Add webapp2 to your app
-----------------------
Create a directory ``hellowebapp2`` for your new app.
`Download webapp2 <http://code.google.com/p/webapp-improved/downloads/list>`_,
unpack it and add ``webapp2.py`` to that directory. If you want to use extra
features such as sessions, extra routes, internationalization and more, also
add the ``webapp2_extras`` directory to your app.


Create an application
---------------------
Create an ``app.yaml`` file in your app directory with the following contents:

.. code-block:: yaml

   application: hellowebapp2
   version: 1
   runtime: python
   api_version: 1

   handlers:
   - url: /.*
     script: main.py

The create a file ``main.py`` and define a handler to display a
'Hello, webapp2!' message::

    import webapp2

    class HelloWebapp2(webapp2.RequestHandler):
        def get(self):
            self.response.write('Hello, webapp2!')

    app = webapp2.WSGIApplication([
        ('/', HelloWebapp2),
    ], debug=True)

    def main():
        app.run()

    if __name__ == '__main__':
        main()

If you're using the Google App Engine Launcher, you can set up the application
by selecting the **File** menu, **Add Existing Application...**, then selecting
the ``hellowebapp2`` directory. Select the application in the app list, click
the Run button to start the application, then click the Browse button to view
it. Clicking Browse simply loads (or reloads)
`http://localhost:8080/ <http://localhost:8080/>`_ in your default web browser.

If you're not using Google App Engine Launcher, start the web server with the
following command, giving it the path to the ``hellowebapp2`` directory:

.. code-block:: bash

   google_appengine/dev_appserver.py helloworld/

The web server is now running, listening for requests on port 8080. You can
test the application by visiting the following URL in your web browser:

    `http://localhost:8080/ <http://localhost:8080/>`_
