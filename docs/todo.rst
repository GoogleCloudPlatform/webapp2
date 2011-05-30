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

    # when you need jinja:
    j = jinja2.get_jinja2(factory=jinja2_factory)


