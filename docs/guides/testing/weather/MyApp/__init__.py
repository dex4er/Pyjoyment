import Pyjoyment


class MyApp(Pyjoyment.object):
    # This method will run once at server start
    def startup(self):
        # Load configuration from config file
        config = self.plugin('YAMLConfig')

        # Configure the application
        self.secrets = config.get('secrets')

        # Router
        r = self.routes

        # Normal route to controller
        r.get('/').to('Example#welcome')

        # NEW: this route only exists if "enable_weather" is set in the configuration
        if config.get('enable_weather'):

            @r.get('/weather')
            def weather(c):
                c.render(text="It's hot! 🔥")


new = MyApp.new
object = MyApp
