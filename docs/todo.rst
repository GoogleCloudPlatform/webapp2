TODO: snippets to document
==========================

Common errors
-------------
- "TypeError: 'unicode' object is not callable": one possible reason is that
  the ``RequestHandler`` returned a string. If the handler returns anything, it
  **must** be a :class:`webapp2.Response` object. Or it must not return
  anything and write to the response instead using ``self.response.write()``.

Secret keys
-----------
Add a note about how to generate strong session secret keys::

    $ openssl genrsa -out ${PWD}/private_rsa_key.pem 2048

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

    # When you need jinja, get it passing the factory.
    j = jinja2.get_jinja2(factory=jinja2_factory)
