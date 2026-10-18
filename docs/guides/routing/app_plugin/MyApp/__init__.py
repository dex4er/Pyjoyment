import Pyjoyment


# Application
class MyApp(Pyjoyment.object):
    def startup(self):

        # Plugin
        self.plugin('MyEmbeddedApp')


new = MyApp.new
object = MyApp
