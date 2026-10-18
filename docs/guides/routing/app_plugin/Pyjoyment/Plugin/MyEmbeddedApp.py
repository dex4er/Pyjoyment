import Pyjoyment.Plugin

import EmbeddedApp


# Plugin
class Pyjoyment_Plugin_MyEmbeddedApp(Pyjoyment.Plugin.object):
    def register(self, app, conf):

        # Automatically add route
        app.routes.any('/foo').set(partial=True).to(app=EmbeddedApp.app)


object = Pyjoyment_Plugin_MyEmbeddedApp
