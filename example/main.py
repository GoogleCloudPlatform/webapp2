from webapp2 import RequestHandler, WSGIApplication, run_wsgi_app


class HomeHandler(RequestHandler):
    def get(self, **kwargs):
        html = '<a href="%s">test item</a>' % self.url_for('view', item='test')
        self.response.out.write(html)


class ViewHandler(RequestHandler):
    def get(self, **kwargs):
        item = kwargs.get('item')
        self.response.out.write('You are viewing item "%s".' % item)


app = WSGIApplication([
    ('/',            'index',     HomeHandler),
    ('/view/{item}', 'view',      ViewHandler),
    ('/lazy',        'lazy-view', 'handlers.LazyHandler'),
], debug=True)


def real_main():
    run_wsgi_app(app)


def profile_main():
    # This is the main function for profiling
    # We've renamed our original main() above to real_main()
    import cProfile, pstats
    prof = cProfile.Profile()
    prof = prof.runctx("real_main()", globals(), locals())
    print "<pre>"
    stats = pstats.Stats(prof)
    stats.sort_stats("time")  # Or cumulative
    stats.print_stats(80)  # 80 = how many to print
    # The rest is optional.
    # stats.print_callees()
    # stats.print_callers()
    print "</pre>"


main = real_main


if __name__ == '__main__':
    main()
