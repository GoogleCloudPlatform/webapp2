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
    Route('/', HomeHandler, name='home'),
    Route('/view/<item>', ViewHandler, name='view'),
    Route('/lazy', 'handlers.LazyHandler', name='lazy'),
    Route('/redirect-me', RedirectHandler, defaults={'url': '/lazy'}),
    Route('/redirect-me2', RedirectHandler, defaults={'url': get_redirect_url}),
    Route('/exception', HandlerWithError),
])


def main():
    app.run()


if __name__ == '__main__':
    main()
