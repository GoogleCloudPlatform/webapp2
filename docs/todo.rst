TODO: snippets to document
==========================

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


i18n with babel
---------------
1) use _() (or gettext()) in your code and templates. Translated strings set in the module globals or class definitions should use some form of lazy gettext(), because i18n won't be available when the modules are imported.

2) Extract all translations using pybabel. Here we pass two directories to be scanned: the templates dir and the app dir. This will create a messages.pot file in the /locale directory with all strings found in these directories. babel.cfg is the extraction configuration that varies depending on the template engine you use:

$ pybabel extract -F ./babel.cfg -o ./locale/messages.pot ./templates/ ./app/
3) Initialize a directory for each language. This is done only once. Here we initialize three translations, en_US, es_ES and pt_BR, and use the messages.pot file created on step 2:

$ pybabel init -l en_US -d ./locale -i ./locale/messages.pot
$ pybabel init -l es_ES -d ./locale -i ./locale/messages.pot
$ pybabel init -l pt_BR -d ./locale -i ./locale/messages.pot
Translate the messages. They will be in .mo files in each translation directory. After all locales are translated, compile them:

$ pybabel compile -f -d ./locale
Later, if new translations are added, repeat step 2 and update them using the new .pot file:

$ pybabel update -l pt_BR -d ./locale/ -i ./locale/messages.pot
Then translate the new strings and compile the translations again.

4) The strategy here may vary. For each request you must set the correct translations to be used, and probably want to cache loaded translations to reuse in subsequent requests. tipfy.ext.i18n has an example for this.
