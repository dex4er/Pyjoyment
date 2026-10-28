import Pyjoyment


# Application
class MyApp(Pyjoyment.object):
    def startup(self):
        # /bye -> MyApp.Controller.Foo.bye
        self.get('/bye').to(controller='foo', action='bye')


new = MyApp.new
object = MyApp
