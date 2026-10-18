import Pyjoyment


# Application
class MyApp(Pyjoyment.object):
    def startup(self):
        # Router
        r = self.routes

        # Route
        r.get('/welcome').to(controller='foo', action='welcome')


new = MyApp.new
object = MyApp
