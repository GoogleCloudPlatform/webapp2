# Copyright 2015 webapp2 AUTHORS.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import webapp2


class HomeHandler(webapp2.RequestHandler):
    def get(self, **kwargs):
        html = '<a href="%s">test item</a>' % self.url_for('view', item='test')
        self.response.out.write(html)


class ViewHandler(webapp2.RequestHandler):
    def get(self, **kwargs):
        item = kwargs.get('item')
        self.response.out.write('You are viewing item "%s".' % item)


class HandlerWithError(webapp2.RequestHandler):
    def get(self, **kwargs):
        raise ValueError('Oops!')


def get_redirect_url(handler, **kwargs):
    return handler.url_for('view', item='i-came-from-a-redirect')


app = webapp2.WSGIApplication([
    # Home sweet home.
    webapp2.Route('/', HomeHandler, name='home'),
    # A route with a named variable.
    webapp2.Route('/view/<item>', ViewHandler, name='view'),
    # Loads a handler lazily.
    webapp2.Route('/lazy', 'handlers.LazyHandler', name='lazy'),
    # Redirects to a given path.
    webapp2.Route(
        '/redirect-me',
        webapp2.RedirectHandler,
        defaults={'url': '/lazy'}),
    # Redirects to a URL using a callable to get the destination URL.
    webapp2.Route(
        '/redirect-me2',
        webapp2.RedirectHandler,
        defaults={'url': get_redirect_url}),
    # No exception should pass. If exceptions are not handled, a 500 page is
    # displayed.
    webapp2.Route('/exception', HandlerWithError),
])
