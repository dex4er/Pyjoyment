import Pyjo.File
import Pyjo.Home
import Pyjoyment


class MyApp(Pyjoyment.object):
    # This method will run once at server start
    def startup(self):
        # Switch to installable home directory
        self.home = Pyjo.Home.new(Pyjo.File.curfile().dirname())

        # Switch to installable "public" directory
        self.static.paths[0] = self.home.child('public')

        # Switch to installable "templates" directory
        self.renderer.paths[0] = self.home.child('templates')

        # Exclude author commands
        self.commands.namespaces = ['Pyjoyment.Command']

        # Load configuration from config file
        config = self.plugin('YAMLConfig')

        # Configure the application
        self.secrets = config.get('secrets')

        # Router
        r = self.routes

        # Normal route to controller
        r.get('/').to('Example#welcome')


new = MyApp.new
object = MyApp
