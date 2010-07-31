from webapp2 import (RedirectHandler, RequestHandler, WSGIApplication,
    run_wsgi_app)


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
    ('/',             HomeHandler,            'home'),
    ('/view/{item}',  ViewHandler,            'view'),
    ('/lazy',         'handlers.LazyHandler', 'lazy'),
    ('/redirect-me',  RedirectHandler,        {'url': '/lazy'}),
    ('/redirect-me2', RedirectHandler,        {'url': get_redirect_url}),
    ('/exception',    HandlerWithError),
], debug=False)


def main():
    run_wsgi_app(app)


if __name__ == '__main__':
    main()
