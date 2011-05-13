from webapp2 import RequestHandler


class LazyHandler(RequestHandler):
    def get(self, **kwargs):
        self.response.out.write('I am a laaazy view.')


class CustomMethodHandler(RequestHandler):
    def custom_method(self):
        self.response.out.write('I am a custom method.')
