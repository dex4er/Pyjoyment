import Pyjoyment


# Application
class MyApp(Pyjoyment.object):
    def startup(self):

        # Plugin
        self.plugin('WerewolfCondition')

        # /hideout (keep them out for 4 days after full moon)
        self.routes.get('/hideout').requires(werewolf=4).to(controller='foo', action='bar')


new = MyApp.new
object = MyApp
