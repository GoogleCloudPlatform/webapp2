TODO: snippets to document
==========================

Jinja2 factory
--------------
To create Jinja2 with custom filters and global variables::

    from webapp2_extras import jinja2

    def jinja2_factory(app):
        j = jinja2.Jinja2(app)
        j.environment.filters.update({
            'my_filter': my_filter,
        })
        j.environment.globals.update({
            'my_global': my_global,
        })
        return j

    # When you need jinja, geti it passing the factory.
    j = jinja2.get_jinja2(factory=jinja2_factory)


Using webapp2 outside of App Engine
-----------------------------------
For dev: install virtualenv, then install packages webapp2, webob and paste
inside a new environment.

Create a ``main.py`` for the app bootstrap::

    import webapp2
    from webapp2_extras import local_app

    class MainHandler(webapp2.RequestHandler):
        def get(self):
            self.response.out.write('Hello, thread-safe world!')

    app = local_app.WSGIApplication([
        ('/.*', MainHandler),
    ], debug=True)

    def main():
        from paste import httpserver
        httpserver.serve(app, host='127.0.0.1', port='8080')

    if __name__ == '__main__':
        main()

And start it using the virtualenv's python:

.. code-block:: bash

   python main.py
