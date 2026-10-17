import Pyjoyment.Plugin

from PluginWithEmbeddedApp import App


class PluginWithEmbeddedApp(Pyjoyment.Plugin.object):
    def register(self, app, conf=None):
        app.routes.any('/plugin').set(partial=True).to(App.app)


object = PluginWithEmbeddedApp
