from webapp2 import RedirectHandler, RequestHandler, Route, WSGIApplication


class HomeHandler(RequestHandler):
    def get(self, **kwargs):
        html = '<a href="%s">test item</a>' % self.url_for('view', item='test')
        self.response.out.write(html)


class ViewHandler(RequestHandler):
    def get(self, **kwargs):
        item = kwargs.get('item')
        self.response.out.write('You are viewing item "%s".' % item)


class HandlerWithError(RequestHandler):
    def get(self, **kwargs):
        raise ValueError('Oops!')


def get_redirect_url(handler, **kwargs):
    return handler.url_for('view', item='i-came-from-a-redirect')


app = WSGIApplication([
    # Home sweet home.
    (Route('/', name='home'), HomeHandler),
    # A route with a named variable.
    (Route('/view/<item>', name='view'), ViewHandler),
    # Loads a handler lazily.
    (Route('/lazy', name='lazy'), 'handlers.LazyHandler'),
    # Redirects to a given path.
    (Route('/redirect-me', defaults={'url': '/lazy'}), RedirectHandler),
    # redirects to a URL using a callable to get the destination URL.
    (Route('/redirect-me2', defaults={'url': get_redirect_url}), RedirectHandler),
    # No exception should pass. If exceptions are not handled, a 500 page is displayed.
    (Route('/exception'), HandlerWithError),
])


def main():
    app.run()


if __name__ == '__main__':
    main()
