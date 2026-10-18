import Pyjoyment


class MyApp(Pyjoyment.object):
    def startup(self):
        # Add another namespace to load commands from
        self.commands.namespaces.append('MyApp.Command')


new = MyApp.new
object = MyApp
