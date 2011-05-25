.. _tutorials.gettingstarted.usingdatastore:

Using the Datastore
===================


Next...
-------
We now have a working guest book application that authenticates users using
Google accounts, lets them submit messages, and displays messages other users
have left. Because App Engine handles scaling automatically, we will not need
to revisit this code as our application gets popular.

This latest version mixes HTML content with the code for the MainPage handler.
This will make it difficult to change the appearance of the application,
especially as our application gets bigger and more complex. Let's use
templates to manage the appearance, and introduce static files for a CSS
stylesheet.

Continue to :ref:`tutorials.gettingstarted.templates`.
