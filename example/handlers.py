import webapp2


class LazyHandler(webapp2.RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('I am a laaazy view.')
