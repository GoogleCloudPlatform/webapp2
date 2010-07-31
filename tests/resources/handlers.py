from webapp2 import RequestHandler


class LazyHandler(RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('I am a laaazy view.')
