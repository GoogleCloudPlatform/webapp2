from __future__ import division

from jinja2.runtime import to_string


name = 'template1.html'


def root(context):
    l_message = context.resolve('message')
    if 0:
        yield None
    yield to_string(l_message)


blocks = {}
debug_info = '1=8'
