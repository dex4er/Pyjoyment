import Pyjoyment


# Application
class MyApp(Pyjoyment.object):
    def startup(self):

        # Check all requests for a "/test" prefix
        @self.hook('before_dispatch')
        def before_dispatch(c):
            if c.req.url.path.contains('/test'):
                c.render(text='This request did not reach the router.')

        # These will not be reached if the hook above renders a response
        r = self.routes
        r.get('/welcome').to('foo#welcome')
        r.post('/bye').to('foo#bye')


new = MyApp.new
object = MyApp
